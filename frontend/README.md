# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Google Search Console OAuth

Set the following variables in a `.env` file before running the app to enable Google Search Console OAuth:

```
VITE_GSC_CLIENT_ID=your_google_client_id
VITE_GSC_REDIRECT_URI=http://localhost:5173/oauth2callback
```

Use the `Connect Google Search Console` card on the home page to start the OAuth flow.
