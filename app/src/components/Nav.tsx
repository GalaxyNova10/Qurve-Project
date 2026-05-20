import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { MagneticButton } from "./MagneticButton";

export function Nav() {
  const links = ["Platform", "Technology", "Architecture", "Research", "Docs"];
  return (
    <motion.header
      initial={{ y: -30, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
      className="fixed top-0 left-0 right-0 z-50"
    >
      <div className="mx-auto max-w-7xl px-6 pt-5">
        <div className="glass-card flex items-center justify-between rounded-full px-5 py-2.5">
          <a href="#" className="flex items-center gap-2.5">
            <div className="relative h-7 w-7">
              <div className="absolute inset-0 rounded-full bg-gradient-to-br from-primary to-accent blur-[6px] opacity-70" />
              <div className="relative h-7 w-7 rounded-full bg-gradient-to-br from-primary via-primary to-accent grid place-items-center">
                <div className="h-2 w-2 rounded-full bg-background" />
              </div>
            </div>
            <span className="font-display text-lg font-semibold tracking-tight">QURVE</span>
          </a>
          <nav className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
            {links.map((l) => (
              <a key={l} href="#" className="hover:text-foreground transition-colors">{l}</a>
            ))}
          </nav>
          <MagneticButton>
            <Link
              to="/login"
              className="relative inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-primary to-accent px-4 py-1.5 text-sm font-medium text-primary-foreground shadow-[0_0_24px_-4px_oklch(0.65_0.27_295/60%)] hover:shadow-[0_0_40px_-4px_oklch(0.65_0.27_295/80%)] transition-shadow"
            >
              Launch Platform
            </Link>
          </MagneticButton>
        </div>
      </div>
    </motion.header>
  );
}
