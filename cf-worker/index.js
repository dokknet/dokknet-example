import { cfWorker } from '@dokknet/paywall-middleware'

const DEBUG = false

addEventListener('fetch', event => {
  try {
    const res = cfWorker.handlePaywall(event).catch(handleError)
    event.respondWith(res)
  } catch (e) {
    event.respondWith(handleError(e))
  }
})

function handleError(e) {
  if (DEBUG) {
    new Response(e.message || e.toString(), { status: 500 })
  } else {
    return new Response('Internal Error', { status: 500 })
  }
}
