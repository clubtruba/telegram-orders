# Mini App publishing checkpoint

This checkpoint publishes only the static Telegram Mini App. It does not modify
the production server, VPN, firewall, Tailscale, DNS, or another Docker stack.

## Prepared locally

- GitHub Pages deployment workflow: `.github/workflows/pages.yml`.
- Target custom domain: `orders.papamio.es`.
- Deployment is manual (`workflow_dispatch`), so pushing the repository cannot
  publish the application by itself.
- The build refuses to run without a full HTTPS API base URL.

## Required facts before approval

1. The GitHub repository and its owner name.
2. The final public HTTPS API base URL, including `/api/v1`.
3. Confirmation that this API permits CORS requests from
   `https://orders.papamio.es`.
4. Confirmation that the API is reachable before the bot receives its Mini App
   button.

## GitHub settings at the publishing checkpoint

1. In repository Settings → Secrets and variables → Actions → Variables, create
   `VITE_API_BASE_URL` with the final HTTPS API base URL.
2. In Settings → Pages, select GitHub Actions as the source and set the custom
   domain to `orders.papamio.es`.
3. Configure the DNS `CNAME` for `orders.papamio.es` to the repository owner's
   `<owner>.github.io` hostname.
4. Run the **Deploy Mini App to GitHub Pages** workflow manually.
5. After GitHub provisions the certificate, enable **Enforce HTTPS**.

Each external operation above remains a separate approval/checkpoint action.
