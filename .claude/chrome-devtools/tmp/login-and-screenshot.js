/**
 * Open browser headed at login page, wait until user reaches /my-account/,
 * then screenshot the profile page in the SAME browser session.
 */
import {
  getBrowser,
  getPage,
  disconnectBrowser,
  outputJSON,
} from 'file:///C:/Users/DongVD/.claude/skills/chrome-devtools/scripts/lib/browser.js'

async function run() {
  const browser = await getBrowser({ headless: false })
  const page = await getPage(browser)

  await page.goto(
    'http://localhost:3000/login/?next=%2Fmy-account%2Fprofile%2F',
    { waitUntil: 'networkidle2' },
  )

  // Wait until the URL contains /my-account/ (user finished login)
  const deadline = Date.now() + 600_000
  while (Date.now() < deadline) {
    if (page.url().includes('/my-account/')) break
    await new Promise((r) => setTimeout(r, 1000))
  }

  if (!page.url().includes('/my-account/')) {
    outputJSON({ success: false, error: 'login timeout', url: page.url() })
    await disconnectBrowser()
    return
  }

  // Ensure on profile page
  await page.goto('http://localhost:3000/my-account/profile/', {
    waitUntil: 'networkidle2',
  })
  await new Promise((r) => setTimeout(r, 1500))

  await page.screenshot({
    path: 'D:\\Freelancer\\Numerlogy\\.claude\\chrome-devtools\\screenshots\\profile-after.png',
    fullPage: true,
  })

  outputJSON({ success: true, url: page.url(), title: await page.title() })
  await disconnectBrowser()
}

run().catch((err) => {
  outputJSON({ success: false, error: err.message, stack: err.stack })
  process.exit(1)
})
