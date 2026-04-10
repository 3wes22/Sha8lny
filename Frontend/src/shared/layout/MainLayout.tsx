import { ReactNode, useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Bell, Compass, LogOut, Menu, Sparkles, User, X } from "lucide-react";

import { type AppRouteMeta, APP_ROUTE_META, PRIMARY_NAV_ITEMS, ROUTES, getRouteMeta } from "@/app/routes";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/context/AuthContext";
import { notificationApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface MainLayoutProps {
  children: ReactNode;
}

interface AtlasNavLinkProps {
  item: AppRouteMeta;
  active: boolean;
  onNavigate?: () => void;
}

const getInitials = (name: string): string => {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
};

const isPrimaryNavActive = (pathname: string, itemPath: string) => {
  if (itemPath === ROUTES.jobs) {
    return pathname === ROUTES.jobs || (/^\/jobs\/[^/]+$/.test(pathname) && pathname !== ROUTES.savedJobs);
  }

  return pathname === itemPath || pathname.startsWith(`${itemPath}/`);
};

const formatNotificationDate = (value: string) =>
  new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });

function AtlasNavLink({ item, active, onNavigate }: AtlasNavLinkProps) {
  const Icon = item.icon;

  return (
    <Link
      className={cn(
        "focus-ring interactive-scale group flex min-w-[132px] flex-1 items-center gap-3 rounded-[1.5rem] px-4 py-3 transition-smooth [--interactive-lift:2px]",
        active
          ? "bg-foreground text-background shadow-soft-lg"
          : "bg-background/55 text-foreground/80 hover:bg-background/82",
      )}
      onClick={onNavigate}
      to={item.path}
    >
      <span
        className={cn(
          "flex h-10 w-10 items-center justify-center rounded-[1rem] border transition-smooth",
          active
            ? "border-background/20 bg-background/10 text-background"
            : "border-border/60 bg-background/60 text-muted-foreground group-hover:text-foreground",
        )}
      >
        {Icon ? <Icon className="h-4 w-4" /> : null}
      </span>
      <span className="min-w-0">
        <span className="block text-[0.72rem] uppercase tracking-[0.22em] opacity-60">
          Atlas route
        </span>
        <span
          className="block truncate text-sm font-medium leading-none"
          style={{ fontFamily: "var(--font-display)" }}
        >
          {item.title}
        </span>
      </span>
    </Link>
  );
}

export function MainLayout({ children }: MainLayoutProps) {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const mobileMenuRef = useRef<HTMLDivElement | null>(null);
  const mobileMenuToggleRef = useRef<HTMLButtonElement | null>(null);
  const { user, logout } = useAuth();
  const [notificationCount, setNotificationCount] = useState(0);
  const [recentNotifications, setRecentNotifications] = useState<
    Array<{ title: string; created_at: string }>
  >([]);
  const currentRoute = useMemo(() => getRouteMeta(location.pathname), [location.pathname]);
  const protectedSurfaces = useMemo(() => APP_ROUTE_META.filter((route) => route.protected), []);
  const surfaceIndex = Math.max(
    protectedSurfaces.findIndex((route) => route.key === currentRoute.key),
    0,
  );
  const surfaceCode = String(surfaceIndex + 1).padStart(2, "0");
  const recentNotification = recentNotifications[0] ?? null;

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!mobileMenuOpen) {
      return;
    }

    const handlePointerDown = (event: MouseEvent | PointerEvent) => {
      const target = event.target as Node | null;

      if (!target) {
        return;
      }

      if (mobileMenuRef.current?.contains(target) || mobileMenuToggleRef.current?.contains(target)) {
        return;
      }

      setMobileMenuOpen(false);
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMobileMenuOpen(false);
        mobileMenuToggleRef.current?.focus();
      }
    };

    window.addEventListener("pointerdown", handlePointerDown);
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("pointerdown", handlePointerDown);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [mobileMenuOpen]);

  useEffect(() => {
    let ignore = false;

    const loadNotifications = async () => {
      try {
        const stats = await notificationApi.getStats();
        if (!ignore) {
          setNotificationCount(stats.unread_count);
          setRecentNotifications(stats.recent_notifications);
        }
      } catch {
        if (!ignore) {
          setNotificationCount(0);
          setRecentNotifications([]);
        }
      }
    };

    void loadNotifications();

    return () => {
      ignore = true;
    };
  }, [location.pathname]);

  const userInitials = user?.full_name
    ? getInitials(user.full_name)
    : user?.username?.slice(0, 2).toUpperCase() || "U";
  const displayName = user?.full_name || user?.username || "User";
  const displayEmail = user?.email || "";
  const utilityLinks = APP_ROUTE_META.filter((route) =>
    [ROUTES.notifications, ROUTES.profile, ROUTES.settings].includes(route.path),
  );
  const mobileAtlasMenu = mobileMenuOpen ? (
    <div
      className="pointer-events-none absolute inset-x-0 top-0 z-50 lg:hidden"
      data-testid="mobile-atlas-menu-layer"
    >
      <div
        className="motion-rise pointer-events-auto ml-auto mr-4 mt-[4.5rem] w-[min(22rem,calc(100vw-1.5rem))] max-h-[min(30rem,calc(100dvh-6rem))] overflow-y-auto rounded-[2rem] border border-border/70 bg-card/96 p-4 shadow-soft-lg backdrop-blur-md sm:mr-6"
        data-testid="mobile-atlas-menu-panel"
        id="mobile-atlas-navigation"
        ref={mobileMenuRef}
      >
        <nav aria-label="Primary navigation" className="grid gap-2">
          {PRIMARY_NAV_ITEMS.map((item) => (
            <AtlasNavLink
              active={isPrimaryNavActive(location.pathname, item.path)}
              item={item}
              key={item.key}
              onNavigate={() => setMobileMenuOpen(false)}
            />
          ))}
        </nav>

        <div className="mt-4 grid gap-2 sm:grid-cols-3">
          {utilityLinks.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                className="focus-ring interactive-scale inline-flex items-center justify-center gap-2 rounded-[1.35rem] border border-border/70 px-3 py-3 text-sm transition-smooth [--interactive-lift:1px] hover:bg-background/72"
                key={item.key}
                onClick={() => setMobileMenuOpen(false)}
                to={item.path}
              >
                {Icon ? <Icon className="h-4 w-4" /> : null}
                {item.title}
              </Link>
            );
          })}
          <button
            className="focus-ring interactive-scale inline-flex items-center justify-center gap-2 rounded-[1.35rem] border border-destructive/30 px-3 py-3 text-sm text-destructive transition-smooth [--interactive-lift:1px] hover:bg-destructive/10 sm:col-span-3"
            onClick={logout}
            type="button"
          >
            <LogOut className="h-4 w-4" />
            Log out
          </button>
        </div>
      </div>
    </div>
  ) : null;

  return (
    <div className="poster-surface min-h-screen overflow-x-clip">
      <div className="pointer-events-none absolute left-[-8rem] top-4 h-80 w-80 bg-[radial-gradient(circle,hsla(20,92%,52%,0.18),transparent_68%)] opacity-80" />
      <div className="pointer-events-none absolute right-[-7rem] top-10 h-72 w-72 bg-[radial-gradient(circle,hsla(188,74%,41%,0.14),transparent_70%)] opacity-80" />
      <div className="relative mx-auto flex min-h-screen w-full max-w-[1600px] flex-col px-3 pb-8 pt-3 sm:px-4 lg:px-6">
        <header className="motion-fade relative">
          <section
            className="gradient-soft relative overflow-hidden rounded-[2.75rem] border border-border/70 bg-card/85 shadow-soft-lg backdrop-blur-md"
            data-testid="atlas-header-shell"
          >
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.75),transparent_28%),radial-gradient(circle_at_left_center,rgba(31,41,55,0.05),transparent_38%)]" />
            <div className="pointer-events-none absolute inset-y-10 left-[34%] hidden w-px bg-border/60 lg:block" />

            <div className="relative px-4 py-4 sm:px-6 sm:py-6 lg:px-8 lg:py-7">
              <div className="flex items-start justify-between gap-3">
                <Link className="focus-ring interactive-scale min-w-0 [--interactive-hover-scale:1.006]" to={ROUTES.dashboard}>
                  <p className="type-kicker">Egypt-first career atlas</p>
                  <div className="mt-3 flex items-end gap-3">
                    <span
                      className="text-[1.75rem] font-bold leading-none text-foreground sm:text-[2.4rem]"
                      style={{ fontFamily: "var(--font-display)" }}
                    >
                      Sha8alny
                    </span>
                    <span className="mb-1 hidden text-xs uppercase tracking-[0.28em] text-muted-foreground sm:inline-flex">
                      workspace
                    </span>
                  </div>
                </Link>

                <div className="relative flex items-center gap-2">
                  <Link
                    className="focus-ring interactive-scale hidden rounded-full border border-border/70 bg-background/65 px-4 py-2 text-sm transition-smooth [--interactive-lift:1px] hover:bg-background/85 sm:inline-flex sm:items-center sm:gap-2"
                    to={ROUTES.notifications}
                  >
                    <Bell className="h-4 w-4" />
                    Alerts
                    <span className="rounded-full bg-foreground px-2 py-0.5 text-[0.68rem] font-semibold text-background">
                      {notificationCount}
                    </span>
                  </Link>
                  <Button
                    aria-expanded={mobileMenuOpen}
                    aria-controls="mobile-atlas-navigation"
                    aria-label={mobileMenuOpen ? "Close atlas navigation" : "Open atlas navigation"}
                    className="h-11 w-11 rounded-full border border-border/70 bg-background/65 hover:bg-background/85 lg:hidden"
                    ref={mobileMenuToggleRef}
                    onClick={() => setMobileMenuOpen((open) => !open)}
                    size="icon"
                    variant="ghost"
                  >
                    {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
                  </Button>
                </div>
              </div>

              <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1.12fr)_minmax(340px,0.88fr)] lg:items-end">
                <div className="space-y-5 motion-rise">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className="type-kicker">Surface {surfaceCode}</span>
                    <span className="rounded-full border border-border/60 px-3 py-1 text-xs uppercase tracking-[0.18em] text-muted-foreground">
                      {currentRoute.title}
                    </span>
                  </div>

                  <div className="max-w-4xl space-y-3">
                    <h2 className="text-balance text-[clamp(3rem,8vw,6.4rem)] font-bold leading-[0.88] text-foreground">
                      {currentRoute.title}
                    </h2>
                    <p className="max-w-2xl text-base leading-7 text-foreground/72 sm:text-lg">
                      {currentRoute.description}
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Link
                      className="focus-ring interactive-scale inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/60 px-4 py-2 text-sm transition-smooth [--interactive-lift:1px] hover:bg-background/82"
                      to={ROUTES.roadmap}
                    >
                      <Compass className="h-4 w-4" />
                      Open roadmap
                    </Link>
                    <Link
                      className="focus-ring interactive-scale inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/60 px-4 py-2 text-sm transition-smooth [--interactive-lift:1px] hover:bg-background/82"
                      to={ROUTES.profile}
                    >
                      <User className="h-4 w-4" />
                      {displayName}
                    </Link>
                    <span className="inline-flex items-center gap-2 rounded-full border border-border/70 bg-background/60 px-4 py-2 text-sm text-muted-foreground">
                      <Sparkles className="h-4 w-4 text-primary" />
                      {notificationCount} unread signals
                    </span>
                  </div>
                </div>

                <div className="space-y-4 lg:pl-8">
                  <div className="shadow-card hidden rounded-[2.1rem] border border-border/70 bg-background/58 p-3 backdrop-blur-md lg:block">
                    <div className="flex items-center justify-between px-2 pb-3">
                      <p className="type-kicker">Island navigation</p>
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
                        Atlas routes
                      </p>
                    </div>
                    <nav aria-label="Primary navigation" className="flex flex-wrap gap-2">
                      {PRIMARY_NAV_ITEMS.map((item) => (
                        <AtlasNavLink
                          active={isPrimaryNavActive(location.pathname, item.path)}
                          item={item}
                          key={item.key}
                        />
                      ))}
                    </nav>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="shadow-card rounded-[1.85rem] border border-border/70 bg-background/48 p-4 backdrop-blur-sm">
                      <p className="type-kicker">Latest signal</p>
                      {recentNotification ? (
                        <>
                          <p
                            className="mt-3 text-xl font-semibold leading-tight text-foreground"
                            style={{ fontFamily: "var(--font-display)" }}
                          >
                            {recentNotification.title}
                          </p>
                          <p className="mt-2 text-sm text-muted-foreground">
                            {formatNotificationDate(recentNotification.created_at)}
                          </p>
                        </>
                      ) : (
                        <>
                          <p
                            className="mt-3 text-xl font-semibold leading-tight text-foreground"
                            style={{ fontFamily: "var(--font-display)" }}
                          >
                            Quiet for now
                          </p>
                          <p className="mt-2 text-sm text-muted-foreground">
                            New roadmap, job, and advisory signals will land here.
                          </p>
                        </>
                      )}
                    </div>

                    <div className="shadow-card rounded-[1.85rem] border border-border/70 bg-background/48 p-4 backdrop-blur-sm">
                      <p className="type-kicker">Operator</p>
                      <div className="mt-3 flex items-center gap-3">
                        <Avatar className="h-11 w-11 border border-border/70">
                          <AvatarImage alt={displayName} src="" />
                          <AvatarFallback className="bg-foreground text-background">
                            {userInitials}
                          </AvatarFallback>
                        </Avatar>
                        <div className="min-w-0">
                          <p
                            className="truncate text-xl font-semibold text-foreground"
                            style={{ fontFamily: "var(--font-display)" }}
                          >
                            {displayName}
                          </p>
                          <p className="truncate text-sm text-muted-foreground">{displayEmail}</p>
                        </div>
                      </div>
                      <div className="mt-4 flex flex-wrap gap-2">
                        {utilityLinks.map((item) => {
                          const Icon = item.icon;
                          return (
                            <Link
                              className="focus-ring interactive-scale inline-flex items-center gap-2 rounded-full border border-border/70 px-3 py-2 text-sm transition-smooth [--interactive-lift:1px] hover:bg-background/82"
                              key={item.key}
                              to={item.path}
                            >
                              {Icon ? <Icon className="h-4 w-4" /> : null}
                              {item.title}
                            </Link>
                          );
                        })}
                        <button
                          className="focus-ring interactive-scale inline-flex items-center gap-2 rounded-full border border-destructive/30 px-3 py-2 text-sm text-destructive transition-smooth [--interactive-lift:1px] hover:bg-destructive/10"
                          onClick={logout}
                          type="button"
                        >
                          <LogOut className="h-4 w-4" />
                          Log out
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
          {mobileAtlasMenu}

        </header>

        <main className="relative z-10 mx-auto w-full max-w-[1520px] flex-1 px-1 pt-6 sm:pt-8">
          {children}
        </main>
      </div>
    </div>
  );
}
