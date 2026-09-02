import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { sdpResults } from './plugins/sdpResults.ts'

// https://vite.dev/config/
export default defineConfig({
  // GitHub Pages serves a project site from /<repo>/, not from the domain root; the deploy
  // workflow passes that prefix in. Dev and local builds keep the plain root.
  base: process.env.VITE_BASE ?? '/',
  plugins: [react(), sdpResults()],
})
