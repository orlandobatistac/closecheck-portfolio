const MEASUREMENT_ID = 'G-6E90E9HB58'

let lastTrackedPage = null

export function trackPageView(pagePath) {
  if (!pagePath || pagePath === lastTrackedPage) {
    return
  }

  lastTrackedPage = pagePath

  if (typeof window === 'undefined' || typeof window.gtag !== 'function') {
    return
  }

  window.gtag('event', 'page_view', {
    send_to: MEASUREMENT_ID,
    page_path: pagePath,
    page_location: window.location.href,
    page_title: document.title,
  })
}