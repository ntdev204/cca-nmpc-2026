# Web operator dashboard

This is a Next.js 16.3.1 App Router dashboard. It polls the Next.js route
handlers, which bridge to the no-ROS TCP backend on Jetson. The interface uses
the CLI-installed shadcn/ui base-nova components with a light, cold-blue theme.

The project was bootstrapped with the official CLI:

```powershell
npx create-next-app@latest app/web --ts --eslint --app --empty --use-npm `
  --import-alias "@/*" --disable-git --yes
```

```powershell
$env:ROBOT_HOST = '100.69.39.18'
$env:ROBOT_PORT = '8765'
npm install
npm run dev
```

Open `http://localhost:3000`. Keep only one motion-capable client connected at
a time; use the web dashboard or the desktop operator app, not both for motion.
The server-side TCP bridge decodes the compressed state/LiDAR/map frames and
keeps the newest stream item, so a slow link cannot build a queue behind
control traffic. It uses a lossless zlib decode and a JSON-bigint parser so
nanosecond timestamps are not rounded by JavaScript before the data reaches
the UI.
