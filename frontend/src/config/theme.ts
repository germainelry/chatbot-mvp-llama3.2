/**
 * Theme system for tenant branding.
 * Loads and applies tenant-specific UI configuration.
 */
import { TenantConfiguration } from '../services/api';

export interface ThemeConfig {
  brandName: string;
  logoUrl?: string;
  primaryColor: string;
  tone: string;
}

const DEFAULT_THEME: ThemeConfig = {
  brandName: 'AI Chatbot Assistant',
  primaryColor: '#3b82f6', // Default blue
  tone: 'professional',
};

let currentTheme: ThemeConfig = DEFAULT_THEME;

/**
 * Convert hex color to HSL format for CSS variables.
 */
function hexToHsl(hex: string): string {
  // Remove # if present
  hex = hex.replace('#', '');
  
  // Parse RGB
  const r = parseInt(hex.substring(0, 2), 16) / 255;
  const g = parseInt(hex.substring(2, 4), 16) / 255;
  const b = parseInt(hex.substring(4, 6), 16) / 255;
  
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;
  
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    
    switch (max) {
      case r:
        h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
        break;
      case g:
        h = ((b - r) / d + 2) / 6;
        break;
      case b:
        h = ((r - g) / d + 4) / 6;
        break;
    }
  }
  
  h = Math.round(h * 360);
  s = Math.round(s * 100);
  const lPercent = Math.round(l * 100);
  
  return `${h} ${s}% ${lPercent}%`;
}

/**
 * Apply theme configuration to the document.
 */
export function applyTheme(config: Partial<TenantConfiguration>): void {
  const uiConfig = config.ui_config || {};
  
  currentTheme = {
    brandName: uiConfig.brand_name || DEFAULT_THEME.brandName,
    logoUrl: uiConfig.logo_url,
    primaryColor: uiConfig.primary_color || DEFAULT_THEME.primaryColor,
    tone: config.tone || DEFAULT_THEME.tone,
  };
  
  // Apply CSS variables - convert hex to HSL format
  const root = document.documentElement;
  try {
    const hslColor = hexToHsl(currentTheme.primaryColor);
    root.style.setProperty('--primary', hslColor);
  } catch (e) {
    console.error('Error converting color to HSL:', e);
    // Fallback to default
    root.style.setProperty('--primary', '199.1 89.1% 48.2%');
  }
  
  // Update document title
  document.title = currentTheme.brandName;
  
  // Store in localStorage for persistence
  localStorage.setItem('theme_config', JSON.stringify(currentTheme));
}

/**
 * Get current theme configuration.
 */
export function getTheme(): ThemeConfig {
  // Try to load from localStorage first
  const stored = localStorage.getItem('theme_config');
  if (stored) {
    try {
      currentTheme = JSON.parse(stored);
    } catch (e) {
      console.error('Error parsing stored theme:', e);
    }
  }
  
  return currentTheme;
}

/**
 * Reset theme to defaults.
 */
export function resetTheme(): void {
  currentTheme = DEFAULT_THEME;
  localStorage.removeItem('theme_config');
  applyTheme({});
}

