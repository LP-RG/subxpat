module madd_i81_o54 (a, b, c, r);
input [26:0] a,b,c;
output [53:0] r;

assign r = (a * b) + c;

endmodule
