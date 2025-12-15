import asyncio
from playwright.async_api import async_playwright

async def capture_screenshots():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        try:
            # Navigate to the application
            await page.goto('http://localhost:5000', wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Screenshot 1: Main Queue Management Tab
            print("Capturing Queue Management tab...")
            await page.screenshot(path='static/screenshots/queue_management.png', full_page=True)
            
            # Click on Analytics tab
            print("Capturing Analytics tab...")
            try:
                await page.click('text=Analytics')
                await asyncio.sleep(2)
                await page.screenshot(path='static/screenshots/analytics_dashboard.png', full_page=True)
            except Exception as e:
                print(f"Error capturing analytics tab: {e}")
            
            # Click on AI Insights tab
            print("Capturing AI Insights tab...")
            try:
                await page.click('text=AI Insights')
                await asyncio.sleep(2)
                await page.screenshot(path='static/screenshots/ai_insights.png', full_page=True)
            except Exception as e:
                print(f"Error capturing AI insights tab: {e}")
            
            # Go back to Queue Management tab and take another screenshot
            print("Capturing Queue Management overview...")
            try:
                await page.click('text=Queue Management')
                await asyncio.sleep(2)
                await page.screenshot(path='static/screenshots/queue_overview.png', full_page=False)
            except Exception as e:
                print(f"Error capturing queue overview: {e}")
            
            print("Screenshots captured successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

# Run the async function
asyncio.run(capture_screenshots())
