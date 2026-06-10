<!-- source: MDN Web Docs | url: https://developer.mozilla.org/en-US/docs/Web/Performance
     license: CC-BY-SA 2.5 or later | attribution: Mozilla Contributors
     fetched: 2026-06-10 -->

# Web performance

Web performance is the objective measurements and the perceived user experience of load time and runtime.
Web performance is how long a site takes to load, become interactive and responsive, and how smooth the content is during user interactions.
Performance concerns questions like: Is scrolling smooth? Are buttons responsive? Do pop-ups load quickly and animate fluidly?
The objective measurements include time to load, frames per second, and time to become interactive, and subjective experience means how long it feels like it takes for content to load.

The longer it takes for a site to respond, the more users will abandon the site. It is important to minimize the loading and response times and add additional features to conceal latency by making the experience as available and interactive as possible, as soon as possible, while asynchronously loading in the longer tail parts of the experience.

There are tools, APIs, and best practices that help us measure and improve web performance. We cover them in the following pages.

## Web performance guides

The Performance guides are resources that describe how browsers work, what affects performance, and how to measure, optimize, and monitor performance across various aspects of your application.

Performance means efficiency. In the context of Open Web Apps, this document explains in general what performance is, how the browser platform helps improve it, and what tools and processes you can use to test and improve it.

Users want web experiences with content that is fast to load and smooth to interact with. Therefore, a developer should strive to achieve these two goals.
To understand how to improve performance and perceived performance, it helps to understand how the browser works.

Latency is the time it takes for a packet of data to travel from source to a destination. In terms of performance optimization, it's important to optimize to reduce causes of latency and to test site performance emulating high latency to optimize for users with slow or unreliable connections.

There are no clear set rules as to what constitutes a slow pace when loading pages, but there are specific guidelines for indicating content will load (1 second), idling (50ms), animating (16.7ms) and responding to user input (50 to 200ms).

DNS-prefetch is an attempt to resolve domain names before resources get requested. This could be a file loaded later or link target a user tries to follow.

Navigation timings are metrics measuring a browser's document navigation events. Resource timings are detailed network timing measurements regarding the loading of an application's resources. Both provide the same read-only properties, but navigation timing measures the main document's timings whereas the resource timing provides the times for all the assets or resources called in by that main document and the resources' requested resources.

Improving your startup performance is often one of the highest value performance optimizations that can be made.
Good user experience includes ensuring your app loads quickly. This article provides performance tips and suggestions for both writing new applications and porting applications to the web from other platforms.

The Critical Rendering Path is the sequence of steps the browser goes through to convert the HTML, CSS, and JavaScript into pixels on the screen. Optimizing the critical render path improves render performance.
The critical rendering path includes the Document Object Model (DOM), CSS Object Model (CSSOM), render tree and layout.

Lazy loading is a strategy to identify resources as non-blocking (non-critical) and load these only when needed. It's a way to shorten the length of the critical rendering path , which translates into reduced page load times.

Speculative loading refers to the practice of performing navigation actions (such as DNS fetching, fetching resources, or rendering documents) before the associated pages are actually visited, based on predictions as to what pages the user is most likely to visit next.

A performance budget is a limit to prevent regressions. It can apply to a file, a file type, all files loaded on a page, a specific metric (e.g., Time to Interactive ), a custom metric (e.g., Time to Hero Element), or a threshold over a period of time.

Synthetic monitoring and real user monitoring (RUM) are two approaches for monitoring and providing insight into web performance. RUM and synthetic monitoring provide for different views of performance and have benefits, good use cases and shortfalls. RUM is generally best suited for understanding long-term trends whereas synthetic monitoring is very well suited to regression testing and mitigating shorter-term performance issues during development. In this article we define and compare these two performance monitoring approaches.

Animations are critical for a pleasurable user experience on many applications. There are many ways to implement web animations, such as CSS transitions / animations or JavaScript-based animations (using requestAnimationFrame() ). In this article, we analyze the performance differences between CSS-based and JavaScript-based animation.

Animation on the web can be done via SVG , JavaScript , including <canvas> and WebGL , CSS animation , <video> , animated GIFs and even animated PNGs and other image types.
The performance cost of animating a CSS property can vary from one property to another, and animating expensive CSS properties can result in Jank as the browser struggles to hit a smooth frame rate .

## Tutorials for beginners

The MDN Web Performance Learning Area contains modern, up-to-date tutorials covering Performance essentials. Start here if you are a newcomer to performance:

This article discusses why web performance is important for accessibility, user experience and your business goals.

You know web performance is important, but what factors affect web performance and how is it measured? This article introduces the components of performance, from web page loading and rendering, including how your content makes it into your users' browser to be viewed, to what groups of people we need to consider when thinking about performance.

More important than how fast your website is in milliseconds, is how fast your users perceive your site to be. These perceptions are impacted by actual page load time, idling, responsiveness to user interaction, and the smoothness of scrolling and other animations. In this article, we discuss the various loading metrics, animation, and responsiveness metrics, along with best practices to improve user perception, if not the actual timings.

Now that you understand a few performance metrics, we take a deeper dive into performance tools, metrics, and APIs and how we can make performance part of the web development workflow.

The lowest hanging fruit of web performance is often media optimization. Serving different media files based on each user agent's capability, size, and pixel density is possible. In this article we discuss the impact images have on performance, and the methods to reduce the number of bytes sent per image.

The lowest hanging fruit of web performance is often media optimization. In this article we discuss the impact video content has on performance, and cover tips like removing audio tracks from background videos can improve performance.

JavaScript, when used properly, can allow for interactive and immersive web experiences — or it can significantly harm download time, render time, in-app performance, battery life, and user experience. This article outlines some JavaScript best practices that should be considered to ensure even complex content is as performant as possible.

Some attributes and the source order of your markup can impact the performance or your website. By minimizing the number of DOM nodes, making sure the best order and attributes are used for including content such as styles, scripts, media, and third-party scripts, you can drastically improve the user experience. This article looks in detail at how HTML can be used to ensure maximum performance.

CSS may be a less important optimization focus for improved performance, but there are some CSS features that impact performance more than others. In this article we look at some CSS properties that impact performance and suggested ways of handling styles to ensure performance is not negatively impacted.

There are many things a developer can do to improve performance, but how fast is fast enough? How can you convince powers that be of the importance of these efforts? Once optimized, how can you ensure bloat doesn't come back? In this article we look at convincing management, developing a performance culture and performance budget, and introduce ways to ensure regressions don't sneak into your code base.

This article covers several topics at a basic level and provides links to deeper dives to improve performance for each topic. In addition to front-end topics such as HTML, CSS, JavaScript, and media files, it also covers APIs, developer tools, best practices, and bad practices relating to web performance.

## Performance APIs

The Performance API is a group of standards used to measure the performance of web applications.
The following pages provide overviews of the Performance APIs including information on how to use them:

The Performance API allows high precision measurements that are based on time in potential sub-millisecond resolution and a stable monotonic clock that is not subject to system clock skew or adjustments.
The high resolution timers are needed for accurate benchmarking instead of the less precise and non-monotonic Date timestamps.

Long animation frames (LoAFs) can impact the user experience of a website.
They can cause slow user interface (UI) updates, resulting in seemingly unresponsive controls and janky (or non-smooth) animated effects and scrolling, leading to user frustration.
The Long Animation Frames API allows developers to get information about the long animation frames and better understand their root causes. This article shows how to use the Long Animation Frames API.

The PerformanceNavigationTiming.notRestoredReasons property reports information on why the current document was blocked from using the bfcache on navigation.
Developers can use this information to identify pages that need updates to make them bfcache-compatible, thereby improving site performance.

Navigation Timing provides metrics associated with navigating from one page to another via the PerformanceNavigationTiming API.
For example, you can determine how much time it takes to load or unload a document, or log the time it took until DOM construction has finished and interaction with the DOM is possible.

The Performance API doesn't provide performance data analysis, or visualizations.
However, the Performance API is integrated well with developer tools and its data is often sent to analytics end points and libraries to record performance metrics which help you to evaluate the data to find performance bottlenecks affecting your users.
This page provides an overview about what sorts of Performance API data exists, how it is collected, and how it can be accessed.

Resource Timing enables retrieving and analyzing detailed network timing data for the loading of an application's resources.
An application can use the timing metrics to determine, for example, the length of time it takes to load a specific resource (such as an image or a script) either implicitly as part of page load or explicitly from JavaScript, for example using the fetch() API.

Server-Timing allows servers to communicate metrics about the request-response cycle to the user agent.
You can collect this information and act on server-side metrics in the same way as all the other metrics processed with the Performance API.

Create application specific timestamps using the user timing API 's "mark" and "measure" entry types using high-precision timestamps that are part of the browser's performance timeline.

### Related APIs

The following APIs are also useful for measuring and influencing page performance:

Provides events you can watch for to know when a document becomes visible or hidden, as well as features to look at the current visibility state of the page.

The Cooperative Scheduling of Background Tasks API (also referred to as the Background Tasks API or the requestIdleCallback() API) provides the ability to queue tasks to be executed automatically by the user agent when it determines that there is free time to do so.

The Beacon interface schedules an asynchronous and non-blocking request to a web server.

The Intersection Observer API provides a way to asynchronously observe changes in the intersection of a target element with an ancestor element or with a top-level document's Viewport .
This enabled use cases such as Timing element visibility to get asynchronously notified when elements of interest become visible.

Exposes decoding and encoding abilities of a client device, such as whether media is supported and whether playback should be smooth and power efficient, with real time feedback about playback to better enable adaptive streaming, and access to display property information.

Information about the system's connection in terms of general connection type (e.g., 'wifi, 'cellular', etc.).
This can be used to select high definition content or low definition content based on the user's connection.

The Battery API , provides information about the system's battery charge level and lets you be notified by events that are sent when the battery level or charging status change.
This can be used to adjust your app's resource usage to reduce battery drain when the battery is low, or to save changes before the battery runs out in order to prevent data loss.

The deviceMemory read-only property of the Navigator interface returns the approximate amount of device memory in gigabytes.

The preloadResponse read-only property of the FetchEvent interface returns a Promise that resolves to the navigation preload Response if navigation preload was triggered, or undefined otherwise.

## Profiling and tooling

This website provides information on how to use and understand the performance features in your developer tools, including Call Tree , Flame Graph , Stack Chart , Marker Chart and Network Chart .

Learn how to profile app performance with Firefox's built-in profiler.

## References

### HTML

- <picture> element

- <video> element

- <source> element

- <img> attributes (like srcset ) for responsive images

- rel="preload" attribute for preloading content via HTML

### CSS

- will-change

### JavaScript

- DOMContentLoaded

- Garbage collection

- requestAnimationFrame

### HTTP

- Content-encoding

- Resource hints via dns-prefetch , preconnect , prefetch , and prerender

- HTTP/2

- Client Hints

## See also

- Responsive images HTML guide

- Web Workers API , including Using Service Workers and Using Web Workers

- Offline and background operation

- Caching

- Client hints

- Glossary terms: Beacon Brotli compression Content Delivery Networks (CDN) Cumulative Layout Shifts (CLS) Code splitting CSSOM Domain sharding Effective connection type First contentful paint (FCP) First CPU idle First paint gzip_compression HTTP/2 HTTP Interaction to next paint (INP) Jank Largest Contentful Paint (LCP) Latency Lazy load Long task Lossless compression Lossy compression Main thread Minification Network throttling Packet Page load time Page prediction Parse Perceived performance Prefetch Prerender QUIC RAIL Real User Monitoring (RUM) Resource Timing Round Trip Time (RTT) Server Timing Speculative parsing Speed index (and Perceptual Speed Index) SSL Synthetic monitoring TCP handshake TCP slow start Transmission Control Protocol (TCP) Time to first byte (TTFB) Time to interactive (TTI) TLS Tree shaking Web performance

- Beacon

- Brotli compression

- Content Delivery Networks (CDN)

- Cumulative Layout Shifts (CLS)

- Code splitting

- CSSOM

- Domain sharding

- Effective connection type

- First contentful paint (FCP)

- First CPU idle

- First paint

- gzip_compression

- HTTP/2

- HTTP

- Interaction to next paint (INP)

- Jank

- Largest Contentful Paint (LCP)

- Latency

- Lazy load

- Long task

- Lossless compression

- Lossy compression

- Main thread

- Minification

- Network throttling

- Packet

- Page load time

- Page prediction

- Parse

- Perceived performance

- Prefetch

- Prerender

- QUIC

- RAIL

- Real User Monitoring (RUM)

- Resource Timing

- Round Trip Time (RTT)

- Server Timing

- Speculative parsing

- Speed index (and Perceptual Speed Index)

- SSL

- Synthetic monitoring

- TCP handshake

- TCP slow start

- Transmission Control Protocol (TCP)

- Time to first byte (TTFB)

- Time to interactive (TTI)

- TLS

- Tree shaking

- Web performance

- Performance in Firefox Developer Tools

## Help improve MDN

This page was last modified on Dec 18, 2025 by MDN contributors .
