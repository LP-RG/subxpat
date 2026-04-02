module madd_i288_o192 (a, b, c, r);
input [95:0] a,b,c;
output [191:0] r;

assign r = (a * b) + c;

endmodule
