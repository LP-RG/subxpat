module abs_diff_i540_o270(a,b,r);
input [269:0] a,b;
output [269:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
