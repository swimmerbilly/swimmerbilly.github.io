interface UnlinkedFilterProps {
  showUnlinkedOnly: boolean;
  onChange: (value: boolean) => void;
  unlinkedCount?: number;
}

export default function UnlinkedFilter({
  showUnlinkedOnly,
  onChange,
  unlinkedCount,
}: UnlinkedFilterProps) {
  return (
    <label className="unlinked-filter">
      <input
        type="checkbox"
        checked={showUnlinkedOnly}
        onChange={(e) => onChange(e.target.checked)}
      />
      Unlinked only
      {unlinkedCount !== undefined && unlinkedCount > 0 && (
        <span className="badge badge-unlinked">{unlinkedCount}</span>
      )}
    </label>
  );
}
