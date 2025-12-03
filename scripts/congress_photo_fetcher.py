import requests
import os
import pandas as pd
import time
import altair as alt
from urllib.parse import quote
import re
from collections import defaultdict

class CongressPhotoFetcher:
    """
    Fetch official congressional photos and enhance visualization data.
    Uses multiple sources to get the most accurate photos available.
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("CONGRESS_API_KEY")
        if not self.api_key:
            raise ValueError("Congress API key required. Set CONGRESS_API_KEY environment variable.")
        
        self.headers = {"X-Api-Key": self.api_key}
        self.photo_cache = {}
        self.members_cache = None  # Cache all members data
        
        # Use a session for connection pooling (faster)
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def fetch_all_members(self):
        """
        Fetch all members from Congress API once and cache them.
        This is much faster than making individual API calls.
        """
        if self.members_cache is not None:
            return self.members_cache
        
        try:
            print("  Fetching all congressional members from API...")
            url = "https://api.congress.gov/v3/member"
            params = {"limit": 250, "offset": 0}
            
            all_members = []
            
            # Fetch first page
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            all_members.extend(data.get("members", []))
            
            # Check if there are more pages
            pagination = data.get("pagination", {})
            total_count = pagination.get("count", 0)
            
            # Fetch remaining pages if needed
            while len(all_members) < total_count:
                params["offset"] = len(all_members)
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                new_members = data.get("members", [])
                if not new_members:
                    break
                all_members.extend(new_members)
                print(f"    Fetched {len(all_members)}/{total_count} members...")
            
            self.members_cache = all_members
            print(f"  Cached {len(all_members)} congressional members")
            return all_members
            
        except Exception as e:
            print(f"    Error fetching members: {e}")
            return []
    
    def get_bioguide_id(self, member_name, birth_year=None, party=None):
        """
        Get the bioguide ID for a member using cached congressional data.
        This is essential for fetching official photos.
        """
        # Check cache first
        cache_key = f"{member_name}_{birth_year}_{party}"
        if cache_key in self.photo_cache:
            return self.photo_cache[cache_key]
        
        try:
            # Get all members (from cache if already fetched)
            all_members = self.fetch_all_members()
            
            # Clean the search name for matching
            search_name = member_name.lower().replace(",", "").replace(".", "").strip()
            name_parts = search_name.split()
            
            # Extract last name and first name (format is usually "Last, First")
            if "," in member_name:
                last_name, first_name = member_name.split(",", 1)
                last_name = last_name.strip().lower()
                first_name = first_name.strip().lower().split()[0]  # Get first word only
            else:
                parts = name_parts
                last_name = parts[-1] if parts else ""
                first_name = parts[0] if len(parts) > 0 else ""
            
            best_match = None
            best_score = 0
            
            for member in all_members:
                api_name = member.get("name", "").lower().replace(",", "").replace(".", "").strip()
                
                # Try exact match first
                if api_name == search_name:
                    bioguide_id = member.get("bioguideId")
                    self.photo_cache[cache_key] = bioguide_id
                    return bioguide_id
                
                # Score-based matching
                score = 0
                api_parts = api_name.split()
                
                # Last name match (most important)
                if last_name and last_name in api_parts:
                    score += 3
                
                # First name match
                if first_name and first_name in api_parts:
                    score += 2
                
                # Birth year match if available
                if birth_year and member.get("birthYear"):
                    try:
                        if int(member.get("birthYear")) == int(birth_year):
                            score += 2
                    except:
                        pass
                
                # Party match
                if party and member.get("partyName"):
                    member_party = member.get("partyName", "")[0].upper()
                    if member_party == party:
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_match = member.get("bioguideId")
            
            # Return best match if score is good enough
            result = best_match if best_score >= 3 else None
            self.photo_cache[cache_key] = result
            return result
            
        except Exception as e:
            print(f"    Error finding bioguide ID for {member_name}: {e}")
            return None
    
    def get_official_photo_url(self, bioguide_id, member_name):
        """
        Get official photo URL using multiple sources.
        Priority: GitHub unitedstates > Bioguide (optimized order for speed)
        """
        if not bioguide_id:
            return None
        
        # Check cache first
        if bioguide_id in self.photo_cache:
            return self.photo_cache[bioguide_id]
        
        # List of photo URLs to try (in order of reliability and speed)
        photo_urls = [
            # Method 1: GitHub congress-legislators photos (most reliable and fast)
            f"https://raw.githubusercontent.com/unitedstates/images/gh-pages/congress/225x275/{bioguide_id}.jpg",
            
            # Method 2: theunitedstates.io mirror (faster than bioguide.gov)
            f"https://theunitedstates.io/images/congress/225x275/{bioguide_id}.jpg",
            
            # Method 3: Original size from GitHub
            f"https://raw.githubusercontent.com/unitedstates/images/gh-pages/congress/original/{bioguide_id}.jpg",
            
            # Method 4: Official Bioguide photos with letter subdirectory
            f"https://bioguide.congress.gov/bioguide/photo/{bioguide_id[0]}/{bioguide_id}.jpg",
            
            # Method 5: Alternative bioguide format
            f"https://bioguide.congress.gov/bioguide/photo/{bioguide_id}.jpg",
        ]
        
        # Try each URL
        for url in photo_urls:
            if self.check_image_exists(url):
                self.photo_cache[bioguide_id] = url
                return url
        
        # Cache negative result too to avoid re-checking
        self.photo_cache[bioguide_id] = None
        print(f"    No photo found for {member_name} ({bioguide_id})")
        return None
    
    def check_image_exists(self, url):
        """Check if an image URL is valid and accessible."""
        try:
            # Use HEAD request first (faster), but fallback to GET if HEAD not supported
            response = self.session.head(url, timeout=3, allow_redirects=True)
            
            # Some servers don't support HEAD, so try GET with small range
            if response.status_code == 405 or response.status_code == 403:
                response = self.session.get(url, timeout=3, stream=True)
                # Read just a tiny bit to verify it's an image
                chunk = next(response.iter_content(chunk_size=1024), None)
                return response.status_code == 200 and chunk is not None
            
            return response.status_code == 200
        except requests.exceptions.Timeout:
            return False
        except Exception:
            return False
    
    def create_fallback_photo_url(self, member_name, party):
        """Create a fallback photo URL with member initials and party colors."""
        name_parts = member_name.replace(",", "").split()
        if len(name_parts) >= 2:
            initials = f"{name_parts[0][:1]}{name_parts[1][:1]}"
        else:
            initials = name_parts[0][:2] if name_parts else "??"
        
        # Party colors
        color_map = {
            'D': '2E86AB',  # Blue
            'R': 'C23B22',  # Red
            'I': '9966CC',  # Purple
            'Unknown': '888888'  # Gray
        }
        
        color = color_map.get(party, '888888')
        return f"https://via.placeholder.com/225x275/{color}/FFFFFF?text={initials}"
    
    def enhance_congress_data_with_photos(self, csv_file_path="../data/congress_individual_members.csv"):
        """
        Load congress data and enhance it with official photos.
        """
        print("Loading congressional data...")
        try:
            df = pd.read_csv(csv_file_path)
        except FileNotFoundError:
            print(f"Error: {csv_file_path} not found. Run python_analyzer.py first.")
            return None
        
        print(f"Processing {len(df)} congressional members...")
        
        # Add photo columns
        df['BioguideID'] = None
        df['OfficialPhotoURL'] = None
        df['PhotoURL'] = None  # Final photo URL (official or fallback)
        
        # Initialize lists to store results
        bioguide_ids = []
        official_photos = []
        final_photos = []
        
        # Process each member
        success_count = 0
        for i in range(len(df)):
            row = df.iloc[i]
            member_name = row['Name']
            party = row['Party']
            birth_year = row.get('BirthYear')
            
            # Print progress every 50 members
            if i % 50 == 0 or i < 10:
                print(f"  Processing {i+1}/{len(df)}: {member_name}")
            
            # Get bioguide ID
            bioguide_id = self.get_bioguide_id(member_name, birth_year, party)
            bioguide_ids.append(bioguide_id)
            
            # Get official photo
            official_photo = None
            if bioguide_id:
                official_photo = self.get_official_photo_url(bioguide_id, member_name)
                if official_photo:
                    success_count += 1
                    if i < 10:  # Show details for first 10
                        print(f"    Found photo for {member_name}")
            official_photos.append(official_photo)
            
            # Set final photo URL (official or fallback)
            final_photo = official_photo or self.create_fallback_photo_url(member_name, party)
            final_photos.append(final_photo)
            
            # Reduced rate limiting for faster processing
            time.sleep(0.05)
        
        # Add all results to dataframe at once
        df['BioguideID'] = bioguide_ids
        df['OfficialPhotoURL'] = official_photos
        df['PhotoURL'] = final_photos
        
        # Save enhanced data
        output_file = "../data/congress_members_with_photos.csv"
        df.to_csv(output_file, index=False)
        
        # Print summary
        official_photos_count = df['OfficialPhotoURL'].notna().sum()
        bioguide_found = df['BioguideID'].notna().sum()
        total_members = len(df)
        
        print(f"\n{'='*60}")
        print(f"Photo enhancement complete!")
        print(f"{'='*60}")
        print(f"� Bioguide IDs found: {bioguide_found}/{total_members} ({bioguide_found/total_members*100:.1f}%)")
        print(f"Official photos found: {official_photos_count}/{total_members} ({official_photos_count/total_members*100:.1f}%)")
        print(f"Fallback photos created: {total_members - official_photos_count}")
        print(f"Enhanced data saved to: {output_file}")
        print(f"{'='*60}")
        
        return df
    
    def process_dataframe(self, df):
        """
        Process a DataFrame and add photo URLs.
        Similar to enhance_congress_data_with_photos but works directly with DataFrames.
        Handles both lowercase_underscore and CapitalCase column names.
        """
        print(f"Processing {len(df)} congressional members...")
        
        # Add photo columns
        df = df.copy()  # Don't modify original
        
        # Initialize lists to store results
        bioguide_ids = []
        final_photos = []
        
        # Process each member
        success_count = 0
        for i in range(len(df)):
            row = df.iloc[i]
            
            # Handle both naming conventions
            member_name = row.get('Name') or row.get('name', 'Unknown')
            party = row.get('Party') or row.get('party', 'Unknown')
            birth_year = row.get('BirthYear') or row.get('birth_year')
            
            # Print progress every 50 members
            if (i + 1) % 50 == 0:
                print(f"  Progress: {i+1}/{len(df)} members...")
            
            # Get bioguide ID
            bioguide_id = self.get_bioguide_id(member_name, birth_year, party)
            bioguide_ids.append(bioguide_id)
            
            # Get official photo
            official_photo = None
            if bioguide_id:
                official_photo = self.get_official_photo_url(bioguide_id, member_name)
                if official_photo:
                    success_count += 1
            
            # Set final photo URL (official or fallback)
            final_photo = official_photo or self.create_fallback_photo_url(member_name, party)
            final_photos.append(final_photo)
            
            # Rate limiting
            time.sleep(0.05)
        
        # Add results to dataframe
        df['BioguideID'] = bioguide_ids
        df['PhotoURL'] = final_photos
        
        # Print summary
        official_photos_count = sum(1 for p in final_photos if p and 'placeholder' not in p)
        bioguide_found = sum(1 for b in bioguide_ids if b)
        total_members = len(df)
        
        print(f"\n{'='*60}")
        print(f"Photo enhancement complete!")
        print(f"{'='*60}")
        print(f"✓ Bioguide IDs found: {bioguide_found}/{total_members} ({bioguide_found/total_members*100:.1f}%)")
        print(f"✓ Official photos found: {official_photos_count}/{total_members} ({official_photos_count/total_members*100:.1f}%)")
        print(f"✓ Fallback photos created: {total_members - official_photos_count}")
        print(f"{'='*60}")
        
        return df
    
    def create_enhanced_visualization(self, df_with_photos):
        """Create enhanced Altair visualization with official photos."""
        
        print("Creating enhanced visualization...")
        
        # Filter out unknown generations for cleaner viz
        df_clean = df_with_photos[df_with_photos['Generation'] != 'Unknown'].copy()
        
        # Create the enhanced scatter plot
        enhanced_chart = alt.Chart(df_clean).mark_circle(
            opacity=0.8,
            stroke='white',
            strokeWidth=1.5,
            size=80
        ).add_params(
            alt.selection_interval(bind='scales')
        ).encode(
            x=alt.X('BirthYear:Q', 
                   title='Birth Year',
                   scale=alt.Scale(domain=[1935, 2005]),
                   axis=alt.Axis(format='d')),
            y=alt.Y('BillCount:Q', 
                   title='Number of Bills Sponsored',
                   scale=alt.Scale(type='sqrt')),  # Square root scale for better distribution
            color=alt.Color('Party:N', 
                           scale=alt.Scale(
                               domain=['D', 'R', 'I'],
                               range=['#2E86AB', '#C23B22', '#9966CC']
                           ),
                           legend=alt.Legend(
                               title='Political Party',
                               titleFontSize=12,
                               labelFontSize=11
                           )),
            size=alt.Size('BillCount:Q', 
                         scale=alt.Scale(range=[50, 300], type='sqrt'),
                         legend=alt.Legend(title='Bills Sponsored')),
            tooltip=[
                alt.Tooltip('Name:N', title='Representative'),
                alt.Tooltip('Party:N', title='Party'),
                alt.Tooltip('Generation:N', title='Generation'),
                alt.Tooltip('BirthYear:Q', title='Birth Year'),
                alt.Tooltip('BillCount:Q', title='Bills Sponsored'),
                alt.Tooltip('PhotoURL:N', title='Photo')  # Official photo in tooltip!
            ]
        ).properties(
            title=alt.TitleParams(
                text='Congressional Members: Legislative Activity by Birth Year',
                subtitle='Circle size represents number of bills sponsored. Hover for official photos.',
                fontSize=16,
                subtitleFontSize=12,
                anchor='start'
            ),
            width=700,
            height=500
        ).configure_axis(
            labelFontSize=11,
            titleFontSize=13,
            grid=True,
            gridOpacity=0.3
        ).configure_view(
            strokeWidth=0
        )
        
        # Save the visualization
        enhanced_chart.save('../visualizations/congress_members_with_photos.html')
        
        print(f"Enhanced visualization saved to: ../visualizations/congress_members_with_photos.html")
        print(f"💡 Hover over any point to see the representative's official photo!")
        
        return enhanced_chart

def main():
    """Main function to run the photo enhancement process."""
    
    print("Congressional Photo Fetcher")
    print("=" * 50)
    
    try:
        # Initialize the fetcher
        fetcher = CongressPhotoFetcher()
        
        # Enhance the data with photos
        df_enhanced = fetcher.enhance_congress_data_with_photos()
        
        if df_enhanced is not None:
            # Create enhanced visualization
            chart = fetcher.create_enhanced_visualization(df_enhanced)
            
            print("\nSuccess! Files created:")
            print("  congress_members_with_photos.csv - Enhanced data with photo URLs")
            print("  congress_members_with_photos.html - Interactive visualization")
            print("\nOpen the HTML file in your browser to explore the interactive chart with photos!")
            
        else:
            print("\nFailed to enhance data. Make sure congress_individual_members.csv exists.")
            
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure your CONGRESS_API_KEY environment variable is set.")

if __name__ == "__main__":
    main()