const express= require("express")
const cors=require("cors")
const { loginController } = require("./controllers/loginController")
const { tripDetails } = require("./controllers/tripdetails")


let app=express()

app.use(express.json())
app.use(cors())

app.post("/login",loginController)
app.post("/shipments",tripDetails)


app.listen("4000",()=>{
    console.log("server is starting")   
})