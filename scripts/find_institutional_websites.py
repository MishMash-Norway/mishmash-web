#!/usr/bin/env python3
"""
Find and populate institutional websites for all people.
Looks up the person's primary institution and fills in their institutional_website field.
"""

import yaml
import argparse
from pathlib import Path
from collections import defaultdict

def load_yaml_file(filepath):
    """Load YAML front matter from a markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.startswith('---'):
            return None
        
        # Split on first --- then second ---
        parts = content.split('---', 2)
        if len(parts) < 2:
            return None
        
        yaml_content = parts[1]
        return yaml.safe_load(yaml_content)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def save_yaml_file(filepath, data, original_content):
    """Save YAML front matter to a markdown file, preserving the original structure."""
    try:
        # Reconstruct the file with updated front matter
        parts = original_content.split('---', 2)
        if len(parts) < 3:
            return False
        
        # Recreate the front matter
        new_front_matter = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
        new_content = f"---\n{new_front_matter}---{parts[2]}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False

def get_institution_website(institution_slug):
    """Get the website URL for an institution."""
    institutions_dir = Path('/home/alexanje/github/mishmash-web/site/_directory/institutions')
    institution_file = institutions_dir / institution_slug / 'index.md'
    
    if not institution_file.exists():
        return None
    
    institution_data = load_yaml_file(institution_file)
    if not institution_data:
        return None
    
    # Check for website URL
    urls = institution_data.get('urls', {})
    if isinstance(urls, dict):
        return urls.get('website') or urls.get('url')
    
    return None

def normalize_institution_slug(institution_ref):
    """Normalize institution reference to slug format."""
    if not institution_ref:
        return None
    
    # Remove /institutions/ prefix if present
    slug = institution_ref.replace('/institutions/', '').replace('/', '')
    return slug if slug else None

def main():
    parser = argparse.ArgumentParser(
        description='Find and populate institutional websites for all people'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Actually update files (default is dry-run)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed information'
    )
    
    args = parser.parse_args()
    
    people_dir = Path('/home/alexanje/github/mishmash-web/site/_directory/people')
    
    missing_institutional = []
    already_have = []
    found_websites = []
    no_institution = []
    institution_not_found = []
    
    for person_file in sorted(people_dir.glob('*/index.md')):
        person_slug = person_file.parent.name
        
        if person_slug == '_template':
            continue
        
        with open(person_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        person_data = load_yaml_file(person_file)
        if not person_data:
            continue
        
        # Get current institutional website
        urls = person_data.get('urls', {})
        current_institutional = urls.get('institutional_website', '')
        
        # Get institution reference
        institution = person_data.get('institution') or (person_data.get('institutions', [None])[0] if person_data.get('institutions') else None)
        
        if not institution:
            no_institution.append(person_slug)
            continue
        
        # Normalize institution slug
        institution_slug = normalize_institution_slug(institution)
        
        if current_institutional:
            # Already has institutional website
            already_have.append((person_slug, institution_slug, current_institutional))
        else:
            # Look up institutional website
            website = get_institution_website(institution_slug)
            
            if website:
                found_websites.append((person_slug, institution_slug, website))
                
                # Update if --update flag is set
                if args.update:
                    if 'urls' not in person_data:
                        person_data['urls'] = {}
                    person_data['urls']['institutional_website'] = website
                    
                    if save_yaml_file(person_file, person_data, original_content):
                        print(f"✓ Updated {person_slug}: {website}")
                    else:
                        print(f"✗ Failed to update {person_slug}")
                else:
                    print(f"  {person_slug} → {website}")
            else:
                institution_not_found.append((person_slug, institution_slug))
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Already have institutional website: {len(already_have)}")
    print(f"Found institutional websites (ready to add): {len(found_websites)}")
    print(f"No institution listed: {len(no_institution)}")
    print(f"Institution not found in directory: {len(institution_not_found)}")
    
    if args.verbose:
        if no_institution:
            print(f"\nNo institution: {', '.join(no_institution[:10])}")
            if len(no_institution) > 10:
                print(f"  ... and {len(no_institution) - 10} more")
        
        if institution_not_found:
            print(f"\nInstitution not found:")
            for person, inst in institution_not_found[:10]:
                print(f"  {person}: {inst}")
            if len(institution_not_found) > 10:
                print(f"  ... and {len(institution_not_found) - 10} more")
    
    if not args.update and found_websites:
        print(f"\nRun with --update flag to populate {len(found_websites)} institutional websites")

if __name__ == '__main__':
    main()
