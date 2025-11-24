import { useEffect, useState, useRef } from "react";
import { useAuth } from "../hooks/useAuth";
import { FaUserCircle } from "react-icons/fa";

export default function Profile() {
  const { user, isAuthenticated } = useAuth();
  const [editMode, setEditMode] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  // Avatar system with DB
  const [avatarUrl, setAvatarUrl] = useState("");
  const fileInputRef = useRef();

  useEffect(() => {
    // Fetch profile with avatar on page load (if not already in user)
    async function fetchProfile() {
      if (!isAuthenticated) return;
      try {
        const token = localStorage.getItem('access_token');
        const res = await fetch("http://localhost:5000/api/profile", {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        const url = data.user?.avatar_url ? `http://localhost:5000${data.user.avatar_url}?v=${Date.now()}` : "";
        setAvatarUrl(url);
        setUsername(data.user?.username || "");
        setEmail(data.user?.email || "");
      } catch (e) {
        setAvatarUrl("");
      }
    }
    fetchProfile();
  }, [isAuthenticated]);

  // Placeholder handlers for demo
  const handleSave = (e) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setEditMode(false);
      setMessage("Profile updated (demo only; backend not implemented).");
      setTimeout(() => setMessage(""), 2500);
    }, 1200);
  };

  const handlePasswordChange = (e) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setPassword("");
      setMessage("Password changed (demo only; backend not implemented).");
      setTimeout(() => setMessage(""), 2500);
    }, 1000);
  };

  const handleAvatarChange = async (e) => {
    const file = e.target.files && e.target.files[0];
    if (file && file.type.startsWith("image/")) {
      const token = localStorage.getItem('access_token');
      const formData = new FormData();
      formData.append("avatar", file);
      setLoading(true);
      try {
        const res = await fetch("http://localhost:5000/api/profile/avatar", {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });
        const data = await res.json();
        if (res.ok && (data.avatar_public_url || data.avatar_url)) {
          const publicUrl = data.avatar_public_url ? `http://localhost:5000${data.avatar_public_url}` : `http://localhost:5000${data.avatar_url}?v=${Date.now()}`;
          setAvatarUrl(publicUrl);
          setMessage("Avatar updated!");
        } else {
          setMessage(data.error || "Avatar update failed");
        }
      } catch (err) {
        setMessage("Avatar upload error");
      }
      setLoading(false);
    }
  };

  const triggerFileSelect = () => fileInputRef.current && fileInputRef.current.click();

  const removeAvatar = async () => {
    setLoading(true);
    setMessage("");
    try {
      const token = localStorage.getItem('access_token');
      await fetch("http://localhost:5000/api/profile/avatar", {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      setAvatarUrl("");
      setMessage("Avatar removed");
    } catch (e) {
      setMessage("Could not remove avatar, try again");
    }
    setLoading(false);
  };

  return (
    <div className="max-w-5xl mx-auto py-8 sm:py-10 px-3 md:px-6">
      <div className="bg-white/95 backdrop-blur rounded-2xl shadow-md sm:shadow-lg p-5 sm:p-8">
        {/* Header + Avatar */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 sm:gap-6 mb-6 sm:mb-8">
          <div className="flex items-center gap-4">
            <div className="relative w-24 h-24 sm:w-28 sm:h-28 shrink-0">
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt="User avatar"
                  className="object-cover w-24 h-24 sm:w-28 sm:h-28 rounded-full ring-4 ring-green-200 shadow"
                />
              ) : (
                <FaUserCircle className="w-24 h-24 sm:w-28 sm:h-28 text-green-400" />
              )}
              <div className="absolute -bottom-2 right-0 flex gap-2">
                <button
                  type="button"
                  className="bg-green-700 text-white rounded-full px-3 py-1 text-xs hover:bg-green-800 transition shadow"
                  onClick={triggerFileSelect}
                  title="Change Avatar"
                  disabled={loading}
                >
                  Edit
                </button>
                {avatarUrl && (
                  <button
                    type="button"
                    className="bg-red-600 text-white rounded-full px-2 py-1 text-xs hover:bg-red-700 transition shadow"
                    onClick={removeAvatar}
                    title="Remove Avatar"
                    disabled={loading}
                  >
                    ×
                  </button>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleAvatarChange}
                />
              </div>
            </div>
            <div className="min-w-0">
              <h1 className="text-xl sm:text-2xl font-bold text-green-900 truncate">Profile & Settings</h1>
              <p className="text-xs sm:text-sm text-gray-500 truncate">Manage your account info and security</p>
            </div>
          </div>
          {message && (
            <div className="text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2 text-sm w-full sm:w-auto">
              {message}
            </div>
          )}
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Profile Info */}
          <section className="bg-white rounded-xl border border-gray-100 p-4 sm:p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-green-800 mb-3">Account</h3>
            {!editMode ? (
              <div className="space-y-3">
                <div className="text-sm"><span className="font-semibold">Name:</span> {username || '-'}</div>
                <div className="text-sm"><span className="font-semibold">Email:</span> {email || '-'}</div>
                <button onClick={() => setEditMode(true)} className="w-full sm:w-auto bg-green-700 text-white px-4 py-2 rounded-lg hover:bg-green-800 transition">
                  Edit Profile
                </button>
              </div>
            ) : (
              <form onSubmit={handleSave} className="space-y-4">
                <div className="flex flex-col">
                  <label className="font-semibold text-sm mb-1">Name</label>
                  <input type="text" className="border rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:outline-none" value={username} onChange={e => setUsername(e.target.value)} required minLength={3} />
                  <p className="text-xs text-gray-500 mt-1">Must be at least 3 characters</p>
                </div>
                <div className="flex flex-col">
                  <label className="font-semibold text-sm mb-1">Email</label>
                  <input type="email" className="border rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:outline-none" value={email} onChange={e => setEmail(e.target.value)} required />
                </div>
                <div className="flex gap-3">
                  <button type="submit" className="bg-green-700 text-white px-4 py-2 rounded-lg hover:bg-green-800 transition w-full sm:w-auto" disabled={loading}>
                    {loading ? "Saving..." : "Save"}
                  </button>
                  <button type="button" onClick={() => setEditMode(false)} className="px-4 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 transition w-full sm:w-auto">
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </section>

          {/* Password Change */}
          <section className="bg-white rounded-xl border border-gray-100 p-4 sm:p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-green-800 mb-3">Change Password</h3>
            <form onSubmit={handlePasswordChange} className="space-y-3">
              <div className="flex flex-col">
                <label className="font-semibold text-sm mb-1">New password</label>
                <input type="password" className="border rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:outline-none" placeholder="Enter a new password" value={password} onChange={e=>setPassword(e.target.value)} minLength={6} required />
                <p className="text-xs text-gray-500 mt-1">Minimum 6 characters</p>
              </div>
              <div>
                <button type="submit" className="w-full sm:w-auto bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition" disabled={loading}>
                  {loading ? "Changing..." : "Change Password"}
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}
