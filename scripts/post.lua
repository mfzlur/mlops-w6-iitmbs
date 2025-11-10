-- This script tells wrk how to format each request.

-- This function is called once per thread
thread.body = '{"features": [5.1, 3.5, 1.4, 0.2]}' -- Example Iris features

-- This function is called for every request
request = function()
  wrk.method = "POST"
  wrk.body = thread.body
  wrk.headers["Content-Type"] = "application/json"
  return wrk.request()
end
