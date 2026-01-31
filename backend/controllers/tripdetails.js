const tripDetails= (req,res)=>{
    const {source,destination,weight,price}=req.body
    console.log(source)
    console.log(destination)
    console.log(weight)
    console.log(price)
    res.status(200).json({"status":"done"})
}

module.exports={
    tripDetails
}