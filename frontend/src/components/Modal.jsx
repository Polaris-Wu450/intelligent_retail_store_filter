function Modal({ isOpen, onClose, title, children, type = 'info', actions }) {
  if (!isOpen) return null;

  const getIconAndColor = () => {
    switch (type) {
      case 'warning':
        return { icon: '⚠️', color: 'text-amber-700', bgColor: 'bg-amber-50', borderColor: 'border-amber-200' };
      case 'error':
        return { icon: '❌', color: 'text-rose-700', bgColor: 'bg-rose-50', borderColor: 'border-rose-200' };
      case 'success':
        return { icon: '✅', color: 'text-emerald-700', bgColor: 'bg-emerald-50', borderColor: 'border-emerald-200' };
      default:
        return { icon: 'ℹ️', color: 'text-sky-700', bgColor: 'bg-sky-50', borderColor: 'border-sky-200' };
    }
  };

  const { icon, color, bgColor, borderColor } = getIconAndColor();

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleOverlayClick}
    >
      <div className={`bg-white rounded-lg shadow-xl max-w-md w-full border-2 ${borderColor}`}>
        {/* Header */}
        <div className={`${bgColor} px-6 py-4 rounded-t-lg`}>
          <div className="flex items-center gap-3">
            <span className="text-2xl">{icon}</span>
            <h3 className={`text-lg font-semibold ${color}`}>{title}</h3>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-5">
          {children}
        </div>

        {/* Actions */}
        <div className="px-6 py-4 bg-gray-50 rounded-b-lg flex gap-3 justify-end">
          {actions}
        </div>
      </div>
    </div>
  );
}

export default Modal;
