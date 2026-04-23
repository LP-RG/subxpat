module mul_i10240_o10240 (a, b, r);
input [5119:0] a,b;
output [10239:0] r;

assign r = a * b;

endmodule
