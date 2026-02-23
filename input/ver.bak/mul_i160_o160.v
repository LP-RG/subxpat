module mul_i160_o160 (a, b, r);
input [79:0] a,b;
output [159:0] r;

assign r = a * b;

endmodule
