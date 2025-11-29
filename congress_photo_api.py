"""
Congress Photo API Client - Refactored for JSON output
Extracts photo fetching logic for serverless use
"""

import requests
import os
import time
from congress_api_client import fetch_congress_members_json, get_generation


class CongressPhotoFetcher:
    """Fetch official congressional photos from multiple sources"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("CONGRESS_API_KEY")
        if not self.api_key:
            raise ValueError("CONGRESS_API_KEY environment variable required")
        
        self.headers = {"X-Api-Key": self.api_key}
        self.photo_cache = {}
        self.members_cache = None
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def fetch_all_members(self):
        """Fetch and cache all members from Congress API"""
        if self.members_cache is not None:
            return self.members_cache
        
        try:
            url = "https://api.congress.gov/v3/member"
            params = {"limit": 250, "offset": 0}
            all_members = []
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            all_members.extend(data.get("members", []))
            
            pagination = data.get("pagination", {})
            total_count = pagination.get("count", 0)
            
            while len(all_members) < total_count:
                params["offset"] = len(all_members)
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                new_members = data.get("members", [])
                if not new_members:
                    break
                all_members.extend(new_members)
            
            self.members_cache = all_members
            return all_members
            
        except Exception:
            return []
    
    def get_bioguide_id(self, member_name, birth_year=None, party=None):
        """Get bioguide ID for a member using cached data"""
        cache_key = f"{member_name}_{birth_year}_{party}"
        if cache_key in self.photo_cache:
            return self.photo_cache[cache_key]
        
        try:
            all_members = self.fetch_all_members()
            search_name = member_name.lower().replace(",", "").replace(".", "").strip()
            name_parts = search_name.split()
            
            if "," in member_name:
                last_name, first_name = member_name.split(",", 1)
                last_name = last_name.strip().lower()
                first_name = first_name.strip().lower().split()[0]
            else:
                parts = name_parts
                last_name = parts[-1] if parts else ""
                first_name = parts[0] if len(parts) > 0 else ""
            
            best_match = None
            best_score = 0
            
            for member in all_members:
                api_name = member.get("name", "").lower().replace(",", "").replace(".", "").strip()
                
                if api_name == search_name:
                    bioguide_id = member.get("bioguideId")
                    self.photo_cache[cache_key] = bioguide_id
                    return bioguide_id
                
                score = 0
                api_parts = api_name.split()
                
                if last_name and last_name in api_parts:
                    score += 3
                if first_name and first_name in api_parts:
                    score += 2
                if birth_year and member.get("birthYear"):
                    try:
                        if int(member.get("birthYear")) == int(birth_year):
                            score += 2
                    except:
                        pass
                if party and member.get("partyName"):
                    member_party = member.get("partyName", "")[0].upper()
                    if member_party == party:
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_match = member.get("bioguideId")
            
            result = best_match if best_score >= 3 else None
            self.photo_cache[cache_key] = result
            return result
            
        except Exception:
            return None
    
    def get_official_photo_url(self, bioguide_id):
        """Get official photo URL from multiple sources"""
        if not bioguide_id:
            return None
        
        if bioguide_id in self.photo_cache:
            return self.photo_cache[bioguide_id]
        
        photo_urls = [
            f"https://raw.githubusercontent.com/unitedstates/images/gh-pages/congress/225x275/{bioguide_id}.jpg",
            f"https://theunitedstates.io/images/congress/225x275/{bioguide_id}.jpg",
            f"https://raw.githubusercontent.com/unitedstates/images/gh-pages/congress/original/{bioguide_id}.jpg",
            f"https://bioguide.congress.gov/bioguide/photo/{bioguide_id[0]}/{bioguide_id}.jpg",
            f"https://bioguide.congress.gov/bioguide/photo/{bioguide_id}.jpg",
        ]
        
        for url in photo_urls:
            if self.check_image_exists(url):
                self.photo_cache[bioguide_id] = url
                return url
        
        self.photo_cache[bioguide_id] = None
        return None
    
    def check_image_exists(self, url):
        """Check if image URL is valid"""
        try:
            response = self.session.head(url, timeout=3, allow_redirects=True)
            
            if response.status_code == 405 or response.status_code == 403:
                response = self.session.get(url, timeout=3, stream=True)
                chunk = next(response.iter_content(chunk_size=1024), None)
                return response.status_code == 200 and chunk is not None
            
            return response.status_code == 200
        except:
            return False
    
    def create_fallback_photo_url(self, member_name, party):
        """Create fallback photo URL with initials and party colors"""
        name_parts = member_name.replace(",", "").split()
        if len(name_parts) >= 2:
            initials = f"{name_parts[0][:1]}{name_parts[1][:1]}"
        else:
            initials = name_parts[0][:2] if name_parts else "??"
        
        color_map = {
            'D': '2E86AB',
            'R': 'C23B22',
            'I': '9966CC',
            'Unknown': '888888'
        }
        
        color = color_map.get(party, '888888')
        return f"https://via.placeholder.com/225x275/{color}/FFFFFF?text={initials}"


def fetch_members_with_photos_json():
    """
    Fetch congressional members with photos as JSON.
    No CSV output - pure API response.
    
    Returns:
        list of dicts with member info + photo URLs
    """
    # First get basic member data
    congress_data = fetch_congress_members_json(detailed_analysis=False)
    members = congress_data['members']
    
    # Initialize photo fetcher
    fetcher = CongressPhotoFetcher()
    
    # Enhance with photos
    for member in members:
        bioguide_id = member.get('bioguide_id')
        name = member.get('name')
        party = member.get('party')
        birth_year = member.get('birth_year')
        
        # Get official photo
        official_photo = None
        if bioguide_id:
            official_photo = fetcher.get_official_photo_url(bioguide_id)
        
        # Set final photo (official or fallback)
        final_photo = official_photo or fetcher.create_fallback_photo_url(name, party)
        
        # Add to member data
        member['official_photo_url'] = official_photo
        member['photo_url'] = final_photo
        
        time.sleep(0.05)
    
    return members
