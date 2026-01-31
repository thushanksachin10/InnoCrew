const loginController= (req,res)=>{
    console.log(req.body.username,req.body.password)
    res.status(200).json({"status":"done"})
}

module.exports={
    loginController
}