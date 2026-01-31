import React, { useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Button,
  Container,
  Card,
  CardContent,
  TextField,
  Grid,
  Avatar,
} from "@mui/material";
import Inventory2OutlinedIcon from "@mui/icons-material/Inventory2Outlined";
import LogoutIcon from "@mui/icons-material/Logout";

const Dashboard = () => {
  const [form, setForm] = useState({
    source: "",
    destination: "",
    weight: "",
    price: "",
  });

  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleAddShipment = async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/shipments`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: JSON.stringify(form),
        }
      );

      if (!res.ok) throw new Error("Failed to add shipment");

      setForm({
        source: "",
        destination: "",
        weight: "",
        price: "",
      });

      alert("Shipment added successfully ✅");
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    window.location.href = "/";
  };

  return (
    <>
      {/* HEADER */}
      <AppBar position="static" color="transparent" elevation={1}>
        <Toolbar sx={{ justifyContent: "space-between" }}>
          <Box display="flex" alignItems="center" gap={2}>
            <Avatar sx={{ bgcolor: "#4f46e5" }}>
              <Inventory2OutlinedIcon />
            </Avatar>
            <Box>
              <Typography fontWeight={600}>Shipment Manager</Typography>
              <Typography variant="body2" color="text.secondary">
                Welcome, manager
              </Typography>
            </Box>
          </Box>

          <Button startIcon={<LogoutIcon />} onClick={handleLogout}>
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      {/* FORM */}
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Card sx={{ borderRadius: 3 }}>
          <CardContent sx={{ p: 4 }}>
            <Typography variant="h6" mb={3}>
              Add New Shipment
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Source"
                  name="source"
                  value={form.source}
                  onChange={handleChange}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Destination"
                  name="destination"
                  value={form.destination}
                  onChange={handleChange}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Weight (kg)"
                  name="weight"
                  value={form.weight}
                  onChange={handleChange}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Price / kg"
                  name="price"
                  value={form.price}
                  onChange={handleChange}
                />
              </Grid>
            </Grid>

            <Button
              variant="contained"
              sx={{ mt: 4, px: 4 }}
              onClick={handleAddShipment}
              disabled={loading}
            >
              {loading ? "Adding..." : "Add Shipment"}
            </Button>
          </CardContent>
        </Card>
      </Container>
    </>
  );
};

export default Dashboard;
