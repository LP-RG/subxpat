module madd_i249_o166 (a, b, c, r);
input [82:0] a,b,c;
output [165:0] r;

assign r = (a * b) + c;

endmodule
