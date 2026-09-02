import { ArrowRight, ShieldCheck, Target, Wallet } from "lucide-react";
import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#09090B] text-white">
      <section className="mx-auto flex min-h-screen max-w-7xl flex-col justify-center px-6 lg:px-12">
        <div className="mb-6 flex w-fit items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm backdrop-blur">
          <ShieldCheck className="h-4 w-4 text-emerald-400" />
          Money with discipline
        </div>

        <h1 className="max-w-4xl text-5xl font-bold leading-tight md:text-7xl">
          Save money.
          <br />
          <span className="text-emerald-400">Without relying on willpower.</span>
        </h1>

        <p className="mt-6 max-w-2xl text-lg text-zinc-400">
          Create goal-based savings vaults, lock your money, build streaks,
          and escape impulsive spending.
        </p>

        <div className="mt-10 flex flex-wrap gap-4">
          <Link
            href="/login"
            className="flex items-center gap-2 rounded-2xl bg-emerald-500 px-6 py-4 font-semibold text-black transition hover:bg-emerald-400"
          >
            Start Saving
            <ArrowRight size={18} />
          </Link>

          <button className="rounded-2xl border border-white/10 bg-white/5 px-6 py-4 font-medium backdrop-blur">
            Watch Demo
          </button>
        </div>

        <div className="mt-20 grid gap-5 md:grid-cols-3">
          {[
            {
              icon: Target,
              title: "Goal Vaults",
              desc: "Dedicated savings for iPhone, Bike, Travel & more."
            },
            {
              icon: Wallet,
              title: "Locked Savings",
              desc: "Easy, Medium & Hard lock modes prevent impulse withdrawals."
            },
            {
              icon: ShieldCheck,
              title: "Emergency Access",
              desc: "OTP + cooldown protects your future self."
            }
          ].map((item) => (
            <div
              key={item.title}
              className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl"
            >
              <item.icon className="mb-4 h-8 w-8 text-emerald-400" />
              <h3 className="text-xl font-semibold">{item.title}</h3>
              <p className="mt-2 text-sm leading-6 text-zinc-400">
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}