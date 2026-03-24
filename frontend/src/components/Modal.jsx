function Modal({ isOpen, onClose, title, children, type = 'info', actions }) {
  if (!isOpen) return null;

  const getIconAndColor = () => {
    switch (type) {
      case 'warning':
        return { icon: '⚠️', color: 'text-yellow-600', bgColor: 'bg-yellow-50' };
      case 'error':
        return { icon: '❌', color: 'text-red-600', bgColor: 'bg-red-50' };
      case 'success':
        return { icon: '✅', color: 'text-green-600', bgColor: 'bg-green-50' };
      default:
        return { icon: 'ℹ️', color: 'text-blue-600', bgColor: 'bg-blue-50' };
    }
  };

  const { icon, color, bgColor } = getIconAndColor();

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
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className={`${bgColor} px-6 py-4 rounded-t-lg border-b`}>
          <div className="flex items-center gap-3">
            <span className="text-2xl">{icon}</span>
            <h3 className={`text-lg font-semibold ${color}`}>{title}</h3>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
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
