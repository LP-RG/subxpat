module madd_i240_o160 (a, b, c, r);
input [79:0] a,b,c;
output [159:0] r;

assign r = (a * b) + c;

endmodule
