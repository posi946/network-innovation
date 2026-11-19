# UptimeRobot setup (Day 5)

1. Create an UptimeRobot account and verify your email.
2. Click **Add New Monitor**.
3. Monitor Type: **HTTP(s)**.
4. URL: `https://api.docusense.africa/health`.
5. Monitoring Interval: **5 minutes**.
6. Alert Contacts: add your email and the Slack webhook integration.
7. Save. The health endpoint returns HTTP 503 when the database is unreachable,
   so Railway restarts the service and UptimeRobot alerts you at the same time.
