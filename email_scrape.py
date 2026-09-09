import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import csv

base_url = "https://cdss.berkeley.edu"
directory_url = f"{base_url}/dsus/data-science-undergraduate-studies-faculty" # Updated to the faculty URL

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def scrape_instructors():
    print(f"Fetching main directory: {directory_url}")
    response = requests.get(directory_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to load page. Status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    profile_links = set()
    
    # 1. Locate the "Data Science Course Instructors" heading
    target_heading = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4', 'h5'] and "Data Science Course Instructors" in tag.get_text())
    
    if not target_heading:
        print("Error: Could not find the 'Data Science Course Instructors' heading on this page.")
        return
        
    print("Found the 'Data Science Course Instructors' section!")

    # 2. Find the container that holds the cards
    section_container = target_heading.find_next_sibling()
    
    if not section_container:
        print("Error: Could not find the content container below the heading.")
        return

    # 3. Extract the links (removing the strict internal-only filter)
    for a_tag in section_container.find_all('a', href=True):
        href = a_tag['href']
        
        # We only want to block direct email links here, but allow external HTTP links
        if href.startswith('mailto:'):
            continue
            
        # We won't strictly enforce '/people/' anymore, so we just add the link
        profile_links.add(href)

    print(f"Found {len(profile_links)} instructor profile links.")
    
    if not profile_links:
        print("Error: No valid links found under this section.")
        return

    print("Starting extraction...\n")
    staff_data = []

    # 4. Visit each individual profile page
    for link in profile_links:
        # urljoin safely handles both internal paths (/people/xyz) and external links (https://eecs...)
        full_url = urljoin(base_url, link) 
        print(f"Scraping: {full_url}")
        
        try:
            prof_resp = requests.get(full_url, headers=headers)
            if prof_resp.status_code != 200:
                print(f"  -> Failed to access (Status {prof_resp.status_code})")
                continue
                
            prof_soup = BeautifulSoup(prof_resp.text, 'html.parser')
            
            # Extract Name (This might fail on external sites if they don't use <h1> for names)
            name_tag = prof_soup.find('h1')
            name = name_tag.get_text(strip=True) if name_tag else "Name not found"
            
            # Extract Email
            email = "Email not found"
            email_tag = prof_soup.find('a', href=lambda href: href and "mailto:" in href)
            
            if email_tag:
                email = email_tag['href'].replace('mailto:', '').strip()
            else:
                text_emails = [word for word in prof_soup.stripped_strings if '@berkeley.edu' in word]
                if text_emails:
                    email = text_emails[0]
                
            staff_data.append({'Name': name, 'Email': email, 'Source URL': full_url})
            time.sleep(1) 
            
        except Exception as e:
            print(f"Error reading {full_url}: {e}")

    # 5. Save to CSV
    csv_filename = 'cdss_instructors.csv'
    # Added 'Source URL' to the CSV so you can manually check the ones that fail
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['Name', 'Email', 'Source URL'])
        writer.writeheader()
        writer.writerows(staff_data)
        
    print(f"\n--- Scraping Complete ---")
    print(f"Successfully extracted {len(staff_data)} records and saved to {csv_filename}.")

if __name__ == "__main__":
    scrape_instructors()