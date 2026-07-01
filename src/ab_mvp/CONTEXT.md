# MVP

Turns a Blueprint into a landing page and deploys it to a URL an experiment can point traffic at. A real Vercel/Netlify/container adapter sits behind the deployer port.

## Language

**Page Artifact**:
The deterministically generated page (HTML + content hash) built from a Blueprint; same blueprint → same artifact.
_Avoid_: page, site, build

**Deployer**:
The port that publishes a page artifact and returns where it went live; stub by default.
_Avoid_: host, publisher (a Publisher posts social content)
