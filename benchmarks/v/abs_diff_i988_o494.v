module abs_diff_i988_o494(a,b,r);
input [493:0] a,b;
output [493:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
