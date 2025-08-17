const hre = require("hardhat");

async function main() {
  console.log("Deploying Settlement contract...");

  const Settlement = await hre.ethers.getContractFactory("Settlement");
  const settlement = await Settlement.deploy();

  await settlement.deployed();

  console.log("Settlement contract deployed to:", settlement.address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });