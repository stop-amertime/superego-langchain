import './app.css'
import App from './App.svelte'
import { mount } from 'svelte'

// Use the Svelte 5 mount API instead of the `new` constructor
const target = document.getElementById('app')

if (target) {
  const app = mount(App, { target })
}

// No export needed for Svelte 5
