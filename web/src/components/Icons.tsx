// Inline stroke icons (Lucide-style paths, MIT) — matches the icon language of the user's Figma frames.
import React, { useId } from "react";

const S = (props: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props} />
);

export const HomeIcon = (p: React.SVGProps<SVGSVGElement>) => (
  <S {...p}><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><path d="M9 22V12h6v10" /></S>
);
export const MapIcon = (p: React.SVGProps<SVGSVGElement>) => (
  <S {...p}><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" /></S>
);
export const CalendarIcon = (p: React.SVGProps<SVGSVGElement>) => (
  <S {...p}><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /></S>
);
export const CrisisIcon = (p: React.SVGProps<SVGSVGElement>) => (
  <S {...p}><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><path d="M12 9v4" /><path d="M12 17h.01" /></S>
);
export const ChartIcon = (p: React.SVGProps<SVGSVGElement>) => (
  <S {...p}><path d="M12 20V10" /><path d="M18 20V4" /><path d="M6 20v-4" /></S>
);
export const ResearchIcon = (p: React.SVGProps<SVGSVGElement>) => (
  <S {...p}><circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" /></S>
);
export const SunIcon = (p: React.SVGProps<SVGSVGElement>) => (
  <S {...p}><circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" /></S>
);
export const MoonIcon = (p: React.SVGProps<SVGSVGElement>) => (
  <S {...p}><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></S>
);
export const GlobeIcon = (p: React.SVGProps<SVGSVGElement>) => (
  <S {...p}><circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" /><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" /></S>
);
/** New brand mark (user's 2026 revamp): gradient flame, right-leaning tip, left lick,
 *  flame-shaped inner cutout (evenodd). Gradient id via useId — safe across instances. */
export const FlameMark = ({ size = 40 }: { size?: number }) => {
  const gid = useId();
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-label="EmberLine emblem">
      <defs>
        <linearGradient id={gid} x1="0.2" y1="0" x2="0.6" y2="1">
          <stop offset="0" stopColor="#F7A75F" />
          <stop offset="1" stopColor="#E8763C" />
        </linearGradient>
      </defs>
      <path fill={`url(#${gid})`} fillRule="evenodd"
        d="M14.3 1.5C14.6 4.0 16.2 5.9 17.4 8.1C18.9 10.9 19.3 13.5 18.7 16.1C17.8 19.7 14.9 22.3 11.5 22.3C8.1 22.3 5.2 19.8 5.0 16.4C4.9 14.4 5.5 12.7 6.5 11.2C6.2 12.8 6.6 14.1 7.7 15.0C7.5 13.3 8.0 11.6 9.1 10.1C11.4 7.4 13.4 4.6 14.3 1.5Z M13.3 11.4C13.7 13.6 14.9 14.7 15.3 16.3C15.7 18.3 14.4 19.9 12.5 19.9C10.8 19.9 9.8 18.5 10.1 16.8C10.4 15.2 11.5 14.3 12.1 12.9C12.5 12.0 13.0 11.8 13.3 11.4Z" />
    </svg>
  );
};
