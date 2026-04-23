module madd_i480_o320 (a, b, c, r);
input [159:0] a,b,c;
output [319:0] r;

assign r = (a * b) + c;

endmodule
