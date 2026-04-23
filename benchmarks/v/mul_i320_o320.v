module mul_i320_o320 (a, b, r);
input [159:0] a,b;
output [319:0] r;

assign r = a * b;

endmodule
