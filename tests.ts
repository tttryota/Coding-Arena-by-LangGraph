

type Option<T> = {
	tag: "some";
	value: T;
} | {
	tag: "none";
}

function showNumberIfExists(obj: Option<number>) {
	if (isSome(obj)) {
		console.log(obj.value)
	}
}

function isSome<T>(obj: Option<T>): obj is { tag: "some", value: T } {
	return obj.tag === "some";
}


function mapOption<T, U>(obj: Option<T>, callback: (value: T) => U): U {
	if (isSome(obj)) {
		return callback(obj.value)
	}
}

const four: Option<number> = { tag: "some", value: 4 }

console.log()