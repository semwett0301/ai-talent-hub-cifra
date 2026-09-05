\# GS Labs Monitoring — UI Guidelines



\## Product



AI-центр мониторинга отраслевых новостей и НПА для PR/GR GS Labs.



Основные продуктовые сценарии:



1\. Новостная лента

2\. Работа с НПА



Раздел "Источники" — настройка системы.



\## Stack



\- React

\- TypeScript

\- Vite

\- Tailwind CSS v4

\- shadcn/ui

\- Base UI

\- Rhea preset

\- React Router

\- Lucide Icons



\## General UI Rules



\- Desktop-first interface.

\- Dark theme only for hackathon MVP.

\- Dense enterprise analytical dashboard.

\- Attached screenshots are the visual source of truth.

\- Use existing shadcn/ui components whenever possible.

\- Do not introduce another UI library.

\- Do not manually recreate standard Button, Input, Select, Dialog, Switch, Tabs, Tooltip or Dropdown components.

\- Custom components should only represent product-specific entities.

\- Compact spacing.

\- High information density.

\- Minimal shadows.

\- Avoid gradients.

\- Avoid excessive rounded corners.

\- Avoid generic SaaS dashboard appearance.



\## Visual Direction



Background: #071426



Surface: #0C1B30



Secondary surface: #11243D



Border: #223750



Primary blue: #2F80ED



Teal / success: #42D392



Warning: #D59A32



Critical: #EF5A5A



Primary text: #F5F7FA



Secondary text: #8FA1B8



\## Layout



Shared application shell:



\- persistent left sidebar;

\- main content area;

\- optional detail panel on the right.



Routes:



\- /news

\- /npa

\- /sources



\## Product-specific components



\### News



\- NewsCard

\- NewsDetails

\- RelevanceBadge

\- AISummaryCard

\- ImpactCard



\### NPA



\- NpaCard

\- NpaDetails

\- NpaDiff

\- NpaVersionHistory

\- NpaAlert



\### Sources



\- SourceRow

\- AddSourceDialog

\- MonitoringRules



\## UX Principles



For news, the user must immediately understand:



1\. What happened?

2\. Why is it relevant for GS Labs?

3\. Does it require action now?



For NPA:



1\. What changed?

2\. What was before?

3\. What is now?

4\. What does the change mean for GS Labs?

