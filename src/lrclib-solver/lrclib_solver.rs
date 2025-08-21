use std::env;



use data_encoding::HEXUPPER;
use ring::digest::{Context, SHA256};

fn verify_nonce(result: &Vec<u8>, target: &Vec<u8>) -> bool {
	if result.len() != target.len() {
		return false;
	}

	for i in 0..(result.len() - 1) {
		if result[i] > target[i] {
			return false;
		} else if result[i] < target[i] {
			break;
		}
	}

	return true;
}

pub fn solve_challenge(prefix: &str, target_hex: &str) -> String {
	let mut nonce = 0;
	let mut hashed;
	let target = HEXUPPER.decode(target_hex.as_bytes()).unwrap();

	loop {
		let mut context = Context::new(&SHA256);
		let input = format!("{}{}", prefix, nonce);
		context.update(input.as_bytes());
		hashed = context.finish().as_ref().to_vec();

		let result = verify_nonce(&hashed, &target);
		if result {
			break;
		} else {
			nonce += 1;
		}
	}

	nonce.to_string()
}


fn main() {
	let args: Vec<String> = env::args().collect();
	if args.len() != 3 {
		eprintln!("Usage: {} <prefix> <target_hex>", args[0]);
		std::process::exit(1);
	}

	let prefix = &args[1];
	let target_hex = &args[2];

	let nonce = solve_challenge(prefix, target_hex);
	println!("{}", nonce);
}
