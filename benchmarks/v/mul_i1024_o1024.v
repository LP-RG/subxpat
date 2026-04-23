module mul_i1024_o1024 (a, b, r);
input [511:0] a,b;
output [1023:0] r;

assign r = a * b;

endmodule
