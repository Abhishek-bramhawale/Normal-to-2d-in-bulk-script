from playwright.sync_api import sync_playwright
import os
import time
import psutil
import shutil

download_folder = os.path.abspath("downloads")
images_folder = os.path.abspath("input")
processed_folder = os.path.abspath("processed")

os.makedirs(download_folder, exist_ok=True)
os.makedirs(images_folder, exist_ok=True)
os.makedirs(processed_folder, exist_ok=True)

brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
user_data_dir = r"C:\Users\Abhishek\AppData\Local\BraveSoftware\Brave-Browser\User Data\Profile 1"

print("Checking if Brave is already running...")
for proc in psutil.process_iter(['name']):
    if proc.info['name'] and 'brave' in proc.info['name'].lower():
        print("⚠️ Close all Brave windows before running this script.")

with sync_playwright() as p:

    browser = p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        executable_path=brave_path,
        accept_downloads=True,
        downloads_path=download_folder,
        viewport={'width': 1280, 'height': 720},
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ]
    )

    page = browser.pages[0] if browser.pages else browser.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    image_files = [
        os.path.join(images_folder, f)
        for f in os.listdir(images_folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
    ]

    if not image_files:
        print("❌ No images found in input folder!")
        browser.close()
        exit(1)

    print(f"Found {len(image_files)} images.")

    # ================= LOOP START =================

    for index, image_path in enumerate(image_files, 1):

        image_name = os.path.basename(image_path)

        print("\n" + "="*60)
        print(f"PROCESSING {index}/{len(image_files)} → {image_name}")
        print("="*60)

        try:

            # Open site
            print("🌐 Opening imagetocartoon...")
            page.goto("https://imagetocartoon.com/", timeout=90000)
            time.sleep(6)

            print("📤 Uploading image...")

            upload_input = page.locator("input[type='file']").first
            upload_input.wait_for(state="attached", timeout=20000)
            upload_input.set_input_files(image_path)

            time.sleep(4)

            print("🎨 Clicking Convert to Cartoon...")

            convert_btn = page.get_by_role("button", name="Convert to Cartoon")
            convert_btn.wait_for(state="visible", timeout=20000)
            convert_btn.click()

            print("⏳ Waiting for processing...")

            download_btn = page.locator("button[title='Download result']")

            download_btn.wait_for(state="visible", timeout=120000)

            print("⬇️ Downloading result...")

            with page.expect_download() as download_info:
                download_btn.click()

            download = download_info.value

            download_path = os.path.join(download_folder, image_name)

            download.save_as(download_path)

            print(f"✅ Downloaded → {download_path}")

            # Move processed image
            dest = os.path.join(processed_folder, image_name)
            shutil.move(image_path, dest)

            print(f"📁 Moved original image → {dest}")

            time.sleep(5)

        except Exception as e:

            print(f"❌ Error processing {image_name}: {e}")

            print("🔄 Reloading page...")
            try:
                page.goto("https://imagetocartoon.com/")
                time.sleep(5)
            except:
                print("Reload failed")

            continue

    # ================= LOOP END =================

    print("\n✅ All images processed.")

    browser.close()
