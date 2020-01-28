(function closure() {
  'use strict'

  var toggleEl = document.getElementById('dokknet-example-paywall-toggle')

  // From https://stackoverflow.com/a/21125098/2650622
  function getCookie(name) {
    var match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'))
    if (match) {
      return match[2]
    }
  }

  function setSendPaywallCookie(value) {
    document.cookie = 'DEBUG_SEND_PAYWALL=' + value + ';Path=/;'
  }

  toggleEl.addEventListener('click', function onClick(event) {
    event.preventDefault()

    if (getCookie('DEBUG_SEND_PAYWALL') === 'true') {
      setSendPaywallCookie('false')
    } else {
      setSendPaywallCookie('true')
    }

    location.reload()
  })
})()