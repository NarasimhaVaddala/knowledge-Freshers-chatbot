from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import word_tokenize
from flask_mail import Mail, Message
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json
nltk.download('punkt_tab')

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

nltk.download("punkt")
app = Flask(__name__)

UNIVERSITIES = {
    "jntuh": {"home": "https://jntuh.ac.in/", "courses": "https://jntuh.ac.in/content/ug-programs/99/42c96486a633f20842b3b37289e8214a"},


    "anurag": {"home": "https://anurag.ac.in/", "courses": "https://anurag.ac.in/programs-offered/" , "images":"https://anurag.ac.in/placements/gallery", "exams":"https://anurag.ac.in/examinations/notifications"  , "location":"https://anurag.ac.in/contact-us" , "placements" :"https://anurag.ac.in/placements/liaison-with-industry/" , "library":"https://anurag.ac.in/library"},



    "malla reddy": {"home": "https://www.mallareddyuniversity.ac.in/", "courses": "https://www.mallareddyuniversity.ac.in/admissions" , "placements":"https://www.mallareddyuniversity.ac.in/placements" , "exams":"https://www.mallareddyuniversity.ac.in/examination-schedules","admissions":"https://www.mallareddyuniversity.ac.in/admissions" , "library":"https://www.mallareddyuniversity.ac.in/library"},



    "sreenidhi":{"home":"https://sreenidhi.edu.in/" , }
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def scrape_university(url, topic, college):
    try:
        session = requests.Session()
        retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)

        logger.debug(f"Scraping {url} for topic: {topic}")
        response = session.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        if college == "jntuh":
            if topic == "courses":
                welcome = soup.find("div", class_="col-md-12")
                if welcome:
                    results.append(welcome.get_text(strip=True))
                if "courses" in UNIVERSITIES[college]:
                    subpage_url = UNIVERSITIES[college]["courses"]
                    sub_response = session.get(subpage_url, headers=HEADERS, timeout=30)
                    sub_soup = BeautifulSoup(sub_response.text, "html.parser")
                    course_content = sub_soup.find_all("p")
                    for p in course_content:
                        text = p.get_text(strip=True)
                        if text and text not in results:
                            results.append(text)
            elif topic == "fees":
                results.append("Fee details are not available on the homepage. Check affiliated college sites or contact the administration.")
            elif topic == "admissions":
                bulletins = soup.find("table", class_="table-striped")
                if bulletins:
                    for tr in bulletins.find_all("tr"):
                        link = tr.find("a", class_="homepagelinks")
                        if link and "admission" in link.text.lower():
                            results.append(f"{link.text.strip()} - {link['href']}")
            elif topic == "location":
                header = soup.find("div", class_="center-text")
                if header:
                    results.append(header.get_text(strip=True))
            elif topic == "placements":
                results.append("Placement details are not directly listed. Check https://jntuh.ac.in/university-industry-interaction-cell.")
            elif topic == "contact":
                email = soup.find("a", href=lambda h: h and "mailto:" in h)
                if email:
                    results.append(email.get_text(strip=True))
            elif topic == "images":
                images = soup.find_all("img", src=True)
                image_urls = [img["src"] if img["src"].startswith("http") else url.rstrip('/') + '/' + img["src"].lstrip('/')
                             for img in images]
                if image_urls:
                    return "<br>".join([f'<img src="{img_url}" alt="{topic}" style="max-width:200px;"/>' for img_url in image_urls])
            elif topic == "all":
                # Fetch all available details
                welcome = soup.find("div", class_="col-md-12")
                if welcome:
                    results.append("Courses:\n" + welcome.get_text(strip=True))
                if "courses" in UNIVERSITIES[college]:
                    subpage_url = UNIVERSITIES[college]["courses"]
                    sub_response = session.get(subpage_url, headers=HEADERS, timeout=30)
                    sub_soup = BeautifulSoup(sub_response.text, "html.parser")
                    course_content = sub_soup.find_all("p")
                    for p in course_content:
                        text = p.get_text(strip=True)
                        if text and text not in results:
                            results.append(text)
                results.append("Fees: Not available on homepage. Contact administration.")
                bulletins = soup.find("table", class_="table-striped")
                if bulletins:
                    admissions = ["Admissions:"]
                    for tr in bulletins.find_all("tr"):
                        link = tr.find("a", class_="homepagelinks")
                        if link and "admission" in link.text.lower():
                            admissions.append(f"{link.text.strip()} - {link['href']}")
                    results.extend(admissions)
                header = soup.find("div", class_="center-text")
                if header:
                    results.append("Location: " + header.get_text(strip=True))
                results.append("Placements: Check https://jntuh.ac.in/university-industry-interaction-cell.")
                email = soup.find("a", href=lambda h: h and "mailto:" in h)
                if email:
                    results.append("Contact: " + email.get_text(strip=True))
                images = soup.find_all("img", src=True)
                image_urls = [img["src"] if img["src"].startswith("http") else url.rstrip('/') + '/' + img["src"].lstrip('/')
                             for img in images]
                if image_urls:
                    results.append("Images:\n" + "<br>".join([f'<img src="{img_url}" alt="image" style="max-width:200px;"/>' for img_url in image_urls]))

        elif college == "anurag":
            if topic == "courses":
                dept_menu = soup.find("ul", id="menu-footer-department-menu")
                if dept_menu:
                    for li in dept_menu.find_all("li"):
                        dept = li.find("a")
                        results.append(f"{dept.text.strip()} - {dept['href']}")
                if "courses" in UNIVERSITIES[college]:
                    subpage_url = UNIVERSITIES[college]["courses"]
                    sub_response = session.get(subpage_url, headers=HEADERS, timeout=30)
                    sub_soup = BeautifulSoup(sub_response.text, "html.parser")
                    course_content = sub_soup.find_all(["h2", "p", "li"])
                    for elem in course_content:
                        text = elem.get_text(strip=True)
                        if text and text not in results:
                            results.append(text)
            
            elif topic == "exams":
                subpage_url = UNIVERSITIES[college]["exams"]
                sub_response = session.get(subpage_url, headers=HEADERS, timeout=30)
                sub_soup = BeautifulSoup(sub_response.text, "html.parser")

                # Find all h2 tags with class 'entry-title'
                h2_tags = sub_soup.find_all("h2", class_="entry-title")

                # Extract text from <a> tags inside those h2 tags
                results = [h2.find("a").get_text(strip=True) for h2 in h2_tags if h2.find("a")]

                # Join and return or print
                combined_result = "\n".join(results)
                print(combined_result)
                results.append(combined_result)



            elif topic == "fees":
                results.append("Fee details are not available on the homepage. Contact the college for more information.")
            elif topic == "admissions":
                contact_section = soup.find("div", class_="et_pb_text_inner")
                if contact_section and "admissions" in contact_section.text.lower():
                    results.append(contact_section.get_text(strip=True))
                phones = soup.find_all("a", href=lambda h: h and "tel:" in h)
                for phone in phones:
                    results.append(f"Contact: {phone.text.strip()}")


            elif topic == "location":

                addr = "Anurag Engineering College \n (An UGC Autonomous Institution) \n  Ananthagiri (V & M), \n Suryapet District, \n Telangana – 508206."
                # footer = sub_soup.find("div", class_="et_pb_blurb_description")
                # combined_result = footer.get_text(strip=True) if footer else "Information not found"
                results.append(addr)


            elif topic == "placements":
                subpage_url = UNIVERSITIES[college]["placements"]
                sub_response = session.get(subpage_url, headers=HEADERS, timeout=30)
                sub_soup = BeautifulSoup(sub_response.text, "html.parser")

                image_spans = sub_soup.find_all("span", class_="et_pb_image_wrap")
                image_urls = []

                for span in image_spans:
                    img_tag = span.find("img")
                    if img_tag:
                        src = img_tag.get("data-src") or img_tag.get("src")
                        if src:
                            # Convert relative to absolute URL
                            if not src.startswith("http"):
                                src = f"https://anurag.ac.in/{src.lstrip('/')}"
                            image_urls.append(src)

                if image_urls:
                    # Return as formatted <img> tags
                    return "<br>".join([
                        f'<img src="{img_url}" alt="placements" style="max-width:200px;"/>' 
                        for img_url in image_urls
                    ])
                else:
                    return "No placement images found."
            

            elif topic == "library":
                subpage_url = UNIVERSITIES[college]["library"]
                sub_response = session.get(subpage_url, headers=HEADERS, timeout=30)
                sub_soup = BeautifulSoup(sub_response.text, "html.parser")

                # Find all matching <div> elements
                library_divs = sub_soup.find_all("div", class_="et_pb_text_inner")

                # Extract and clean text
                library_texts = [div.get_text(strip=True) for div in library_divs if div.get_text(strip=True)]

                if library_texts:
                    results.append("<br><br>".join(library_texts))
                    
                else:
                    results.append("No library information found.")


            elif topic == "contact":
                footer_contacts = soup.find_all("div", class_="et_pb_blurb_container")
                for contact in footer_contacts:
                    text = contact.get_text(strip=True)
                    if text:
                        results.append(text)
            elif topic == "images":
                subpage_url = UNIVERSITIES[college]["images"]
                sub_response = session.get(subpage_url, headers=HEADERS, timeout=30)
                sub_soup = BeautifulSoup(sub_response.text, "html.parser")  # 👈 FIXED

                images = sub_soup.find_all("img", src=True)
                image_urls = [img["data-src"] if img.get("data-src") else img["src"]
                            for img in images if img.get("data-src") or img.get("src")]

                image_urls = [url if url.startswith("http") else f"https://anurag.ac.in/{url.lstrip('/')}" for url in image_urls]

                if image_urls:
                    return "<br>".join([f'<img src="{img_url}" alt="{topic}" style="max-width:200px;"/>' for img_url in image_urls])

            elif topic == "all":
                dept_menu = soup.find("ul", id="menu-footer-department-menu")
                if dept_menu:
                    results.append("Courses:")
                    for li in dept_menu.find_all("li"):
                        dept = li.find("a")
                        results.append(f"{dept.text.strip()} - {dept['href']}")
                if "courses" in UNIVERSITIES[college]:
                    subpage_url = UNIVERSITIES[college]["courses"]
                    sub_response = session.get(subpage_url, headers=HEADERS, timeout=30)
                    sub_soup = BeautifulSoup(sub_response.text, "html.parser")
                    course_content = sub_soup.find_all(["h2", "p", "li"])
                    for elem in course_content:
                        text = elem.get_text(strip=True)
                        if text and text not in results:
                            results.append(text)
                results.append("Fees: Not available on homepage. Contact the college.")
                contact_section = soup.find("div", class_="et_pb_text_inner")
                if contact_section and "admissions" in contact_section.text.lower():
                    results.append("Admissions: " + contact_section.get_text(strip=True))
                phones = soup.find_all("a", href=lambda h: h and "tel:" in h)
                if phones:
                    results.append("Admissions Contact:")
                    for phone in phones:
                        results.append(phone.text.strip())
                footer = soup.find("div", class_="et_pb_text_inner")
                if footer and "Ananthagiri" in footer.text:
                    results.append("Location: " + footer.get_text(strip=True))
                placement_section = soup.find("div", class_="et_pb_promo_description")
                if placement_section and "Placements" in placement_section.text:
                    results.append("Placements: " + placement_section.get_text(strip=True))
                    link = placement_section.find_next("a", class_="et_pb_promo_button")
                    if link:
                        results.append(f"More info: {link['href']}")
                footer_contacts = soup.find_all("div", class_="et_pb_blurb_container")
                if footer_contacts:
                    results.append("Contact:")
                    for contact in footer_contacts:
                        text = contact.get_text(strip=True)
                        if text:
                            results.append(text)
                images = soup.find_all("img", src=True)
                image_urls = [img["data-src"] if img.get("data-src") else img["src"]
                             for img in images if img.get("data-src") or img.get("src")]
                image_urls = [url if url.startswith("http") else f"https://anurag.ac.in/{url.lstrip('/')}" for url in image_urls]
                if image_urls:
                    results.append("Images:\n" + "<br>".join([f'<img src="{img_url}" alt="image" style="max-width:200px;"/>' for img_url in image_urls]))

        elif college == "malla reddy":
            if topic == "courses" or topic == "course":
                if "courses" in UNIVERSITIES[college]:
                    subpage_url = UNIVERSITIES[college]["courses"]
                    sub_response = session.get(subpage_url, headers=HEADERS, timeout=30)
                    sub_soup = BeautifulSoup(sub_response.text, "html.parser")
                    course_content = sub_soup.find_all(["h1", "h2", "p", "li"])
                    for elem in course_content:
                        text = elem.get_text(strip=True)
                        if text and text not in results:
                            results.append(text)
            elif topic == "fees":
                results.append("Fee details are not available on the homepage. Contact the university for more information.")
            elif topic == "admissions":
                dynamic_model_url = "https://www.mallareddyuniversity.ac.in/_api/v2/dynamicmodel"
                dm_response = session.get(dynamic_model_url, headers=HEADERS, timeout=30)
                if dm_response.ok:
                    dm_data = json.loads(dm_response.text)
                    if "admissions" in str(dm_data).lower():
                        results.append("Admissions info available in dynamic model. Contact the university for details.")
                results.append("Contact for admissions: https://www.mallareddyuniversity.ac.in/contact.")
            elif topic == "location":
                warmup_script = soup.find("script", id="wix-essential-viewer-model")
                if warmup_script:
                    viewer_model = json.loads(warmup_script.text)
                    events_data = viewer_model.get("appsWarmupData", {}).get("140603ad-af8d-84a5-2c80-a0f60cb47351", {})
                    for event in events_data.get("widgetcomp-kmorhm3j", {}).get("events", {}).get("events", []):
                        location = event.get("location", {}).get("address", "")
                        if location:
                            results.append(location)
                            break
                if not results:
                    results.append("Maisammaguda, Dulapally, Hyderabad, Telangana 500043, India")
            elif topic == "placements":
                if "placements" in UNIVERSITIES[college]:
                    subpage_url = UNIVERSITIES[college]["placements"]                    
                    sub_response = session.get(subpage_url, headers=HEADERS, timeout=30)
                    sub_soup = BeautifulSoup(sub_response.text, "html.parser")
                    # print(sub_soup.prettify())
                    element = sub_soup.find(id="comp-kn15oyxy")
                    if element:
                        items = element.find_all("li")
                        results = [item.get_text(strip=True) for item in items]
                        combined_result = "\n".join(results)
                        print(combined_result)
                    else:
                        print("Element with ID 'comp-kn15oyxy' not found.")
                results.append("Placement details are not directly listed. Check https://www.mallareddyuniversity.ac.in/placements.")
            elif topic == "exams":
                if "exams" in UNIVERSITIES[college]:
                    subpage_url = UNIVERSITIES[college]["exams"]                    
                    sub_response = session.get(subpage_url, headers=HEADERS, timeout=30)
                    sub_soup = BeautifulSoup(sub_response.text, "html.parser")
                    spans = sub_soup.find_all("span")
                    results = [span.get_text(strip=True) for span in spans if span.get_text(strip=True)]
                    combined_result = "\n".join(results)
                    print(combined_result)
                    results.append(combined_result)

            elif topic == "library":
                if "library" in UNIVERSITIES[college]:
                    subpage_url = UNIVERSITIES[college]["library"] 
                    sub_response = session.get(subpage_url, headers=HEADERS, timeout=30)
                    sub_soup = BeautifulSoup(sub_response.text, "html.parser")
                    spans = sub_soup.find_all("span")
                    results = [span.get_text(strip=True) for span in spans if span.get_text(strip=True)]
                    combined_result = "\n".join(results)
                    print(combined_result)
                    results.append(combined_result)
            elif topic == "contact":
                results.append("Contact info not on homepage. Try: https://www.mallareddyuniversity.ac.in/contact.")
            elif topic == "images":
                images = soup.find_all("img", src=True)
                image_urls = [img["src"] if img["src"].startswith("http") else url.rstrip('/') + '/' + img["src"].lstrip('/')
                             for img in images]
                warmup_script = soup.find("script", id="wix-essential-viewer-model")
                if warmup_script:
                    viewer_model = json.loads(warmup_script.text)
                    events_data = viewer_model.get("appsWarmupData", {}).get("140603ad-af8d-84a5-2c80-a0f60cb47351", {})
                    for event in events_data.get("widgetcomp-kmorhm3j", {}).get("events", {}).get("events", []):
                        img_url = event.get("mainImage", {}).get("url", "")
                        if img_url and img_url not in image_urls:
                            image_urls.append(img_url)
                if image_urls:
                    return "<br>".join([f'<img src="{img_url}" alt="{topic}" style="max-width:200px;"/>' for img_url in image_urls])
            elif topic == "all":
                if "courses" in UNIVERSITIES[college]:
                    subpage_url = UNIVERSITIES[college]["courses"]
                    sub_response = session.get(subpage_url, headers=HEADERS, timeout=30)
                    sub_soup = BeautifulSoup(sub_response.text, "html.parser")
                    course_content = sub_soup.find_all(["h1", "h2", "p", "li"])
                    results.append("Courses:")
                    for elem in course_content:
                        text = elem.get_text(strip=True)
                        if text and text not in results:
                            results.append(text)
                results.append("Fees: Not available on homepage. Contact the university.")
                dynamic_model_url = "https://www.mallareddyuniversity.ac.in/_api/v2/dynamicmodel"
                dm_response = session.get(dynamic_model_url, headers=HEADERS, timeout=30)
                if dm_response.ok:
                    dm_data = json.loads(dm_response.text)
                    if "admissions" in str(dm_data).lower():
                        results.append("Admissions: Info in dynamic model. Contact for details.")
                results.append("Admissions Contact: https://www.mallareddyuniversity.ac.in/contact.")
                warmup_script = soup.find("script", id="wix-essential-viewer-model")
                if warmup_script:
                    viewer_model = json.loads(warmup_script.text)
                    events_data = viewer_model.get("appsWarmupData", {}).get("140603ad-af8d-84a5-2c80-a0f60cb47351", {})
                    for event in events_data.get("widgetcomp-kmorhm3j", {}).get("events", {}).get("events", []):
                        location = event.get("location", {}).get("address", "")
                        if location:
                            results.append("Location: " + location)
                            break
                if "Location" not in "\n".join(results):
                    results.append("Location: Maisammaguda, Dulapally, Hyderabad, Telangana 500043, India")
                results.append("Placements: Check https://www.mallareddyuniversity.ac.in/placements.")
                results.append("Contact: Try https://www.mallareddyuniversity.ac.in/contact.")
                images = soup.find_all("img", src=True)
                image_urls = [img["src"] if img["src"].startswith("http") else url.rstrip('/') + '/' + img["src"].lstrip('/')
                             for img in images]
                if warmup_script:
                    viewer_model = json.loads(warmup_script.text)
                    events_data = viewer_model.get("appsWarmupData", {}).get("140603ad-af8d-84a5-2c80-a0f60cb47351", {})
                    for event in events_data.get("widgetcomp-kmorhm3j", {}).get("events", {}).get("events", []):
                        img_url = event.get("mainImage", {}).get("url", "")
                        if img_url and img_url not in image_urls:
                            image_urls.append(img_url)
                if image_urls:
                    results.append("Images:\n" + "<br>".join([f'<img src="{img_url}" alt="image" style="max-width:200px;"/>' for img_url in image_urls]))

        elif college == "sreenidhi":
            if topic == "location":
                results.append("Sreenidhi Institute of Science & Technology \n Yamnampet, Ghatkesar Hyderabad - 501 301, \n Telangana. info@sreenidhi.edu.in")
            if topic == "images":
                results.append("kjashdkhas")


        if results:
            combined_result = "\n".join(results)
            logger.debug(f"Found {len(results)} items for {topic}: {combined_result[:100]}...")
            return combined_result
        else:
            logger.debug(f"No {topic} data found on {url}")
            return f"No {topic} data found on {url}. Please try another topic."
    except requests.RequestException as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        return f"Sorry, couldn’t fetch data from {url} due to a connection issue. Try again later!"

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'rajashekar5092@gmail.com'
app.config['MAIL_PASSWORD'] = 'rdtx estt mipo excc'
mail = Mail(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chatbot")
def chatbot():
    college = request.args.get("college", "").lower()
    if college not in UNIVERSITIES:
        return "Invalid college selected!", 400
    return render_template("chatbot.html", college=college)

@app.route("/get_response", methods=["POST"])
def get_response():
    data = request.json
    user_message = data.get("message", "").lower()
    college = data.get("college", "").lower()
    
    if college not in UNIVERSITIES:
        return jsonify({"response": "Invalid college!"}), 400

    logger.debug(f"Received message: {user_message} for college: {college}")
    tokens = word_tokenize(user_message)
    topics = ["courses", "fees", "admissions", "location", "placements", "contact", "images", "all", "exams" , "library"]
    topic = next((t for t in topics if t in tokens), None)
    
    if topic:
        url = UNIVERSITIES[college]["home"] if topic != "courses" else UNIVERSITIES[college].get("courses", UNIVERSITIES[college]["home"])
        scraped_data = scrape_university(url, topic, college)
        response = f"{college.capitalize()} {topic}:\n{scraped_data}"
    else:
        response = f"What would you like to know about {college.capitalize()}? Try asking about courses, fees, admissions, location, placements, contact, images, or all."
    
    logger.debug(f"Response: {response[:100]}...")
    return jsonify({"response": response})

@app.route("/submit_feedback", methods=["POST"])
def sendMail():
    feedback = request.json.get("feedback", "")
    if not feedback:
        return jsonify({"response": "Feedback is empty!"}), 400
    try:
        msg = Message(
            subject="New Feedback Received",
            sender=app.config['MAIL_USERNAME'],
            recipients=["narasimhavaddala@gmail.com"],
            body=f"Feedback received:\n\n{feedback}"
        )
        mail.send(msg)
        return jsonify({"response": "Feedback sent successfully!"})
    except Exception as e:
        logger.error(f"Error sending feedback: {e}")
        return jsonify({"response": "Failed to send feedback!"}), 500

if __name__ == "__main__":
    app.run(debug=True)