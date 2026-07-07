import type { Plugin } from "@opencode-ai/plugin"

const palette = [
  "#1f77b4",
  "#aec7e8",
  "#ff7f0e",
  "#ffbb78",
  "#2ca02c",
  "#98df8a",
  "#d62728",
  "#ff9896",
  "#9467bd",
  "#c5b0d5",
  "#8c564b",
  "#c49c94",
  "#e377c2",
  "#f7b6d2",
  "#7f7f7f",
  "#c7c7c7",
  "#bcbd22",
  "#dbdb8d",
  "#17becf",
  "#9edae5",
] as const

const tab20: Plugin = async () => ({
  config(cfg) {
    const agents = cfg.agent ?? {}
    for (const [index, name] of Object.keys(agents).sort().entries()) {
      if (agents[name]?.color) continue
      agents[name] = { ...agents[name], color: palette[index % palette.length] }
    }
    cfg.agent = agents
  },
})

export default tab20
