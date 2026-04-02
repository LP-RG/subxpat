module madd_i162_o108 (a, b, c, r);
input [53:0] a,b,c;
output [107:0] r;

assign r = (a * b) + c;

endmodule
