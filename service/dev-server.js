// Local stand-in for Vercel: same routes as vercel.json, preferences kept in memory.
//   DATA_BASE=http://localhost:8001 node dev-server.js   (default port 3000)
const http = require("http");
const fs = require("fs");
const path = require("path");
const addon = require("./api/addon");
const prefs = require("./api/prefs");

const page = path.join(__dirname, "configure.html");
http.createServer((req, res) => {
  const p = req.url.split("?")[0];
  if (p === "/" || p === "/configure" || /^\/[^/]+\/configure$/.test(p) || p === "/configure.html") {
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    return res.end(fs.readFileSync(page));
  }
  if (p === "/api/prefs") return prefs(req, res);
  req.url = "/api/addon?p=" + req.url.replace(/^\//, ""); // the catch-all rewrite
  return addon(req, res);
}).listen(process.env.PORT || 3000, () => console.log(`http://localhost:${process.env.PORT || 3000}`));
