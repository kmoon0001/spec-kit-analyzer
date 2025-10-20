type Status = "ready" | "warming" | "offline" | "warning";

type Props = {
  label: string;
  status: Status;
};

const COLOR_MAP: Record<Status, string> = {
  ready: "rgba(34,197,94,0.25)",
  warming: "rgba(59,130,246,0.25)",
  offline: "rgba(148,163,184,0.2)",
  warning: "rgba(244,114,182,0.25)",
};

const TEXT_MAP: Record<Status, string> = {
  ready: "#bbf7d0",
  warming: "#bfdbfe",
  offline: "#cbd5f5",
  warning: "#fbcfe8",
};

export const StatusChip = ({ label, status }: Props) => {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.35rem",
        padding: "0.25rem 0.55rem",
        borderRadius: "999px",
        background: COLOR_MAP[status],
        color: TEXT_MAP[status],
        fontSize: "0.75rem",
        fontWeight: 600,
        letterSpacing: "0.02em",
      }}
    >
      <span
        style={{
          width: "8px",
          height: "8px",
          borderRadius: "50%",
          background: TEXT_MAP[status],
        }}
      />
      {label}
    </span>
  );
};
