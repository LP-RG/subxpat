module madd_i213_o142 (a, b, c, r);
input [70:0] a,b,c;
output [141:0] r;

assign r = (a * b) + c;

endmodule
